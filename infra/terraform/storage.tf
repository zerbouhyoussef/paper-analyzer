resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  blob_properties {
    delete_retention_policy {
      days = 7
    }
  }

  tags = local.default_tags
}

resource "azurerm_storage_container" "papers" {
  name                  = "papers"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

resource "azurerm_storage_queue" "processing" {
  name                 = "paper-processing"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_share" "data" {
  name               = "paper-data"
  storage_account_id = azurerm_storage_account.main.id
  quota              = 10
}
