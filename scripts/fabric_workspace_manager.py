# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Fabric workspace management utilities for auto-creating workspaces and managing permissions."""

import sys
from typing import Optional
import requests
from azure.identity import ClientSecretCredential


def get_access_token(token_credential) -> str:
    """Get Fabric API access token from credential.
    
    Args:
        token_credential: Azure credential for authentication
        
    Returns:
        Bearer token string
        
    Raises:
        Exception: If token acquisition fails
    """
    try:
        token = token_credential.get_token("https://api.fabric.microsoft.com/.default")
        return token.token
    except Exception as e:
        raise Exception(f"Failed to acquire access token: {str(e)}")


def validate_workspace_creator_permission(token_credential) -> tuple[bool, str]:
    """Validate that the service principal has permission to create workspaces.
    
    This attempts to list workspaces to verify basic API access. Full validation of 
    workspace creator permission happens when attempting actual workspace creation.
    
    Args:
        token_credential: Azure credential for authentication
        
    Returns:
        Tuple of (has_permission: bool, error_message: str)
    """
    try:
        token = get_access_token(token_credential)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test API access by listing workspaces
        list_url = "https://api.fabric.microsoft.com/v1/workspaces"
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return True, ""
        elif response.status_code == 401:
            return False, "Authentication failed. Check AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
        elif response.status_code == 403:
            return False, "Service Principal lacks permissions to access Fabric API. Ensure it has 'Workspace Creator' role in Fabric Admin Portal."
        else:
            return False, f"Fabric API returned status {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "Request to Fabric API timed out. Check network connectivity."
    except Exception as e:
        return False, f"Failed to validate permissions: {str(e)}"


def check_workspace_exists(workspace_name: str, token_credential) -> Optional[str]:
    """Check if a workspace with the given name exists.
    
    Args:
        workspace_name: Name of the workspace to check (e.g., "[D] Fabric Blueprint")
        token_credential: Azure credential for authentication
        
    Returns:
        Workspace ID if exists, None if not found
        
    Raises:
        Exception: If API call fails
    """
    try:
        token = get_access_token(token_credential)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        list_url = "https://api.fabric.microsoft.com/v1/workspaces"
        response = requests.get(list_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to list workspaces. Status: {response.status_code}, Response: {response.text}")
        
        workspaces = response.json().get("value", [])
        for workspace in workspaces:
            if workspace.get("displayName") == workspace_name:
                workspace_id = workspace.get("id")
                print(f"  ✓ Workspace '{workspace_name}' already exists (ID: {workspace_id})")
                return workspace_id
        
        return None
        
    except requests.exceptions.Timeout:
        raise Exception("Request to Fabric API timed out while checking workspace existence")
    except Exception as e:
        raise Exception(f"Failed to check workspace existence: {str(e)}")


def create_workspace(workspace_name: str, capacity_id: str, token_credential) -> str:
    """Create a new Fabric workspace with the specified capacity.
    
    Args:
        workspace_name: Display name for the new workspace
        capacity_id: Fabric capacity ID (GUID) - mandatory
        token_credential: Azure credential for authentication
        
    Returns:
        Workspace ID of the newly created workspace
        
    Raises:
        Exception: If workspace creation fails
    """
    try:
        if not capacity_id:
            raise Exception("Capacity ID is required for workspace creation. Set FABRIC_CAPACITY_ID_* secrets in GitHub.")
        
        token = get_access_token(token_credential)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        create_url = "https://api.fabric.microsoft.com/v1/workspaces"
        payload = {
            "displayName": workspace_name,
            "capacityId": capacity_id
        }
        
        print(f"  → Creating workspace '{workspace_name}' with capacity '{capacity_id}'...")
        response = requests.post(create_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 201:
            workspace_id = response.json().get("id")
            print(f"  ✓ Workspace created successfully (ID: {workspace_id})")
            return workspace_id
        elif response.status_code == 400:
            error_detail = response.json().get("error", {}).get("message", response.text)
            raise Exception(f"Invalid workspace creation request: {error_detail}")
        elif response.status_code == 403:
            raise Exception(
                "Service Principal lacks 'Workspace Creator' permission. "
                "Grant this permission in Fabric Admin Portal → Tenant Settings → Developer Settings → "
                "Service Principals can create and edit Fabric workspaces."
            )
        elif response.status_code == 404:
            raise Exception(f"Invalid capacity ID '{capacity_id}'. Verify FABRIC_CAPACITY_ID_* secret is correct.")
        else:
            raise Exception(f"Workspace creation failed. Status: {response.status_code}, Response: {response.text}")
            
    except requests.exceptions.Timeout:
        raise Exception("Request to Fabric API timed out while creating workspace")
    except Exception as e:
        if "Workspace Creator" in str(e) or "capacity" in str(e).lower():
            raise  # Re-raise with original message for configuration errors
        raise Exception(f"Failed to create workspace: {str(e)}")


def add_workspace_admin(workspace_id: str, service_principal_object_id: str, token_credential) -> None:
    """Add a service principal as admin to a workspace.
    
    Args:
        workspace_id: GUID of the workspace
        service_principal_object_id: Azure AD Object ID of the service principal (NOT Client ID)
        token_credential: Azure credential for authentication
        
    Raises:
        Exception: If role assignment fails
    """
    try:
        if not service_principal_object_id:
            print("  ⚠ WARNING: DEPLOYMENT_SP_OBJECT_ID not set. Skipping role assignment.")
            print("    The workspace was created but the service principal may not have admin access.")
            print("    You may need to manually grant admin permissions in Fabric portal.")
            return
        
        token = get_access_token(token_credential)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Add role assignment
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/roleAssignments"
        payload = {
            "principal": {
                "id": service_principal_object_id,
                "type": "ServicePrincipal"
            },
            "role": "Admin"
        }
        
        print(f"  → Adding Service Principal as Admin to workspace...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"  ✓ Service Principal added as Admin successfully")
        elif response.status_code == 400:
            error_detail = response.json().get("error", {}).get("message", response.text)
            # Check if SP already has access
            if "already exists" in error_detail.lower() or "already assigned" in error_detail.lower():
                print(f"  ✓ Service Principal already has Admin access")
            else:
                raise Exception(f"Invalid role assignment request: {error_detail}")
        elif response.status_code == 404:
            raise Exception(
                f"Invalid Service Principal Object ID '{service_principal_object_id}'. "
                "Verify DEPLOYMENT_SP_OBJECT_ID secret contains the Azure AD Object ID (not Client ID). "
                "Find it in Azure Portal → Azure Active Directory → Enterprise Applications → search by Client ID → Object ID."
            )
        else:
            raise Exception(f"Role assignment failed. Status: {response.status_code}, Response: {response.text}")
            
    except requests.exceptions.Timeout:
        raise Exception("Request to Fabric API timed out while assigning workspace role")
    except Exception as e:
        if "Object ID" in str(e):
            raise  # Re-raise with original message for configuration errors
        raise Exception(f"Failed to add Service Principal as workspace admin: {str(e)}")


def ensure_workspace_exists(
    workspace_name: str,
    capacity_id: str,
    service_principal_object_id: str,
    token_credential
) -> str:
    """Ensure workspace exists, creating it if necessary.
    
    This is the main entry point for workspace management. It checks if the workspace
    exists, creates it if needed, and ensures the service principal has admin access.
    
    Args:
        workspace_name: Display name of the workspace (e.g., "[D] Fabric Blueprint")
        capacity_id: Fabric capacity ID for the environment
        service_principal_object_id: Azure AD Object ID of the deployment service principal
        token_credential: Azure credential for authentication
        
    Returns:
        Workspace ID (either existing or newly created)
        
    Raises:
        Exception: If workspace cannot be created or accessed
    """
    try:
        print(f"→ Ensuring workspace '{workspace_name}' exists...")
        
        # Check if workspace already exists
        workspace_id = check_workspace_exists(workspace_name, token_credential)
        
        if workspace_id:
            # Workspace exists, no need to create
            return workspace_id
        
        # Workspace doesn't exist, create it
        print(f"  ℹ Workspace not found, creating new workspace...")
        workspace_id = create_workspace(workspace_name, capacity_id, token_credential)
        
        # Add service principal as admin
        add_workspace_admin(workspace_id, service_principal_object_id, token_credential)
        
        print(f"  ✓ Workspace '{workspace_name}' is ready for deployment")
        return workspace_id
        
    except Exception as e:
        # Provide helpful error message with configuration hints
        error_msg = str(e)
        print(f"\n✗ ERROR: Failed to ensure workspace exists: {error_msg}\n")
        
        # Add troubleshooting hints
        if "Workspace Creator" in error_msg:
            print("TROUBLESHOOTING:")
            print("  1. Open Fabric Admin Portal (https://app.fabric.microsoft.com/admin-portal)")
            print("  2. Navigate to: Tenant Settings → Developer Settings")
            print("  3. Enable: 'Service Principals can create and edit Fabric workspaces'")
            print("  4. Add your Service Principal to the allowed list")
            print()
        elif "capacity" in error_msg.lower():
            print("TROUBLESHOOTING:")
            print("  1. Verify FABRIC_CAPACITY_ID_* secrets are set in GitHub repository")
            print("  2. Get capacity ID from Fabric portal: Settings → Admin Portal → Capacity Settings")
            print("  3. Ensure capacity is active and not paused")
            print()
        elif "Object ID" in error_msg:
            print("TROUBLESHOOTING:")
            print("  1. Go to Azure Portal → Azure Active Directory → Enterprise Applications")
            print("  2. Search for your application by Client ID (Application ID)")
            print("  3. Copy the 'Object ID' field (NOT the Application ID)")
            print("  4. Set DEPLOYMENT_SP_OBJECT_ID secret to this Object ID value")
            print()
        
        raise
