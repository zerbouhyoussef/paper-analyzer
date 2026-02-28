output "resource_group_name" {
  description = "Name of the Azure resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_connection_string" {
  description = "Storage account connection string"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "container_registry_login_server" {
  description = "ACR login server URL for pushing images"
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
}

output "container_registry_admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "api_url" {
  description = "Public URL of the API service"
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "ui_url" {
  description = "Public URL of the UI service"
  value       = "https://${azurerm_container_app.ui.ingress[0].fqdn}"
}

output "search_endpoint" {
  description = "Azure AI Search endpoint URL"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "search_api_key" {
  description = "Azure AI Search primary API key"
  value       = azurerm_search_service.main.primary_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for querying logs"
  value       = azurerm_log_analytics_workspace.main.id
}
