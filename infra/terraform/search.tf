resource "azurerm_search_service" "main" {
  name                = "search-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "basic"

  tags = local.default_tags
}

resource "azurerm_key_vault_secret" "search_endpoint" {
  name         = "search-endpoint"
  value        = "https://${azurerm_search_service.main.name}.search.windows.net"
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "search_api_key" {
  name         = "search-api-key"
  value        = azurerm_search_service.main.primary_key
  key_vault_id = azurerm_key_vault.main.id
}
