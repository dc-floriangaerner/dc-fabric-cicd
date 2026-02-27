terraform {
  required_version = ">= 1.8, < 2.0"

  required_providers {
    fabric = {
      source  = "microsoft/fabric"
      version = "~> 1.7"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-fabric-cicd-tfstate"
    storage_account_name = "stsfabriccicdtfstate"
    container_name       = "tfstate"
    # key is supplied at init time via -backend-config so each repository and
    # environment gets its own isolated state file (for example <org>/<repo>/dev.tfstate)
  }
}

provider "fabric" {}

# ──────────────────────────────────────────────
# Workspaces
# ──────────────────────────────────────────────

resource "fabric_workspace" "fabric_blueprint" {
  display_name = var.workspace_name
  capacity_id  = var.capacity_id
}

# ──────────────────────────────────────────────
# Entra Admin Group → Admin on each workspace
# ──────────────────────────────────────────────

resource "fabric_workspace_role_assignment" "fabric_blueprint_admin_group" {
  workspace_id = fabric_workspace.fabric_blueprint.id
  principal = {
    id   = var.entra_admin_group_object_id
    type = "Group"
  }
  role = "Admin"
}
