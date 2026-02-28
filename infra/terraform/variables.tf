variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "paper-analyzer"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"
}

variable "openai_api_key" {
  description = "OpenAI API key for the enricher service"
  type        = string
  sensitive   = true
}

variable "openai_model" {
  description = "OpenAI model to use for summarization"
  type        = string
  default     = "gpt-4.1-mini"
}

variable "api_container_image" {
  description = "Container image for the API service"
  type        = string
  default     = ""
}

variable "ui_container_image" {
  description = "Container image for the UI service"
  type        = string
  default     = ""
}

variable "ingestor_container_image" {
  description = "Container image for the ingestor service"
  type        = string
  default     = ""
}

variable "extractor_container_image" {
  description = "Container image for the extractor service"
  type        = string
  default     = ""
}

variable "validator_container_image" {
  description = "Container image for the validator service"
  type        = string
  default     = ""
}

variable "enricher_container_image" {
  description = "Container image for the enricher service"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default     = {}
}

locals {
  prefix = "${var.project_name}-${var.environment}"
  # Storage account names: alphanumeric only, 3-24 chars
  storage_account_name = replace(substr("${var.project_name}${var.environment}sa", 0, 24), "-", "")

  default_tags = merge(var.tags, {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  })
}
