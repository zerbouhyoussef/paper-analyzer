resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.prefix}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.default_tags
}

resource "azurerm_container_app_environment_storage" "data" {
  name                         = "paper-data"
  container_app_environment_id = azurerm_container_app_environment.main.id
  account_name                 = azurerm_storage_account.main.name
  share_name                   = azurerm_storage_share.data.name
  access_key                   = azurerm_storage_account.main.primary_access_key
  access_mode                  = "ReadWrite"
}

# ── API service (always-on) ─────────────────────────────────────────────────────

resource "azurerm_container_app" "api" {
  name                         = "ca-api-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  tags                         = local.default_tags

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }

  secret {
    name  = "search-api-key"
    value = azurerm_search_service.main.primary_key
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 3

    volume {
      name         = "paper-data"
      storage_name = azurerm_container_app_environment_storage.data.name
      storage_type = "AzureFile"
    }

    container {
      name   = "api"
      image  = var.api_container_image != "" ? var.api_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/api:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }

      env {
        name  = "DATA_DIR"
        value = "/data"
      }

      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = "https://${azurerm_search_service.main.name}.search.windows.net"
      }

      env {
        name        = "AZURE_SEARCH_API_KEY"
        secret_name = "search-api-key"
      }

      volume_mounts {
        name = "paper-data"
        path = "/app/data"
      }
    }
  }
}

# ── UI service (always-on) ──────────────────────────────────────────────────────

resource "azurerm_container_app" "ui" {
  name                         = "ca-ui-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"
  tags                         = local.default_tags

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 8501

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 1
    max_replicas = 2

    container {
      name   = "ui"
      image  = var.ui_container_image != "" ? var.ui_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/ui:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "API_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }
    }
  }
}

# ── Pipeline jobs (on-demand) ───────────────────────────────────────────────────

resource "azurerm_container_app_job" "ingestor" {
  name                         = "job-ingestor-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 1800
  replica_retry_limit          = 1
  tags                         = local.default_tags

  manual_trigger_config {}

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "storage-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  template {
    volume {
      name         = "paper-data"
      storage_name = azurerm_container_app_environment_storage.data.name
      storage_type = "AzureFile"
    }

    container {
      name   = "ingestor"
      image  = var.ingestor_container_image != "" ? var.ingestor_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/ingestor:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "AZURE_CONNECTION_STRING"
        secret_name = "storage-connection-string"
      }

      env {
        name  = "AZURE_CONTAINER_NAME"
        value = "papers"
      }

      env {
        name  = "AZURE_QUEUE_NAME"
        value = "paper-processing"
      }

      volume_mounts {
        name = "paper-data"
        path = "/app/data"
      }
    }
  }
}

resource "azurerm_container_app_job" "extractor" {
  name                         = "job-extractor-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 3600
  replica_retry_limit          = 1
  tags                         = local.default_tags

  manual_trigger_config {}

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  template {
    volume {
      name         = "paper-data"
      storage_name = azurerm_container_app_environment_storage.data.name
      storage_type = "AzureFile"
    }

    container {
      name   = "extractor"
      image  = var.extractor_container_image != "" ? var.extractor_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/extractor:latest"
      cpu    = 1.0
      memory = "2Gi"

      volume_mounts {
        name = "paper-data"
        path = "/app/data"
      }
    }
  }
}

resource "azurerm_container_app_job" "validator" {
  name                         = "job-validator-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 600
  replica_retry_limit          = 1
  tags                         = local.default_tags

  manual_trigger_config {}

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  template {
    volume {
      name         = "paper-data"
      storage_name = azurerm_container_app_environment_storage.data.name
      storage_type = "AzureFile"
    }

    container {
      name   = "validator"
      image  = var.validator_container_image != "" ? var.validator_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/validator:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      volume_mounts {
        name = "paper-data"
        path = "/app/data"
      }
    }
  }
}

resource "azurerm_container_app_job" "enricher" {
  name                         = "job-enricher-${local.prefix}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  container_app_environment_id = azurerm_container_app_environment.main.id
  replica_timeout_in_seconds   = 3600
  replica_retry_limit          = 1
  tags                         = local.default_tags

  manual_trigger_config {}

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }

  secret {
    name  = "search-api-key"
    value = azurerm_search_service.main.primary_key
  }

  template {
    volume {
      name         = "paper-data"
      storage_name = azurerm_container_app_environment_storage.data.name
      storage_type = "AzureFile"
    }

    container {
      name   = "enricher"
      image  = var.enricher_container_image != "" ? var.enricher_container_image : "${azurerm_container_registry.main.login_server}/paper-analyzer/enricher:latest"
      cpu    = 1.0
      memory = "2Gi"

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }

      env {
        name  = "OPENAI_MODEL"
        value = var.openai_model
      }

      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = "https://${azurerm_search_service.main.name}.search.windows.net"
      }

      env {
        name        = "AZURE_SEARCH_API_KEY"
        secret_name = "search-api-key"
      }

      volume_mounts {
        name = "paper-data"
        path = "/app/data"
      }
    }
  }
}
