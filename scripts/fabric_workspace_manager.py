# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Fabric workspace management utilities for auto-creating workspaces and managing permissions."""

from typing import Optional, Union, Literal
import requests
from azure.identity import ClientSecretCredential, DefaultAzureCredential

# Constants
ERROR_TEXT_MAX_LENGTH = 500
DEFAULT_TIMEOUT = 30
CREATE_WORKSPACE_TIMEOUT = 60
FABRIC_API_BASE_URL = "https://api.fabric.microsoft.com"
FABRIC_TOKEN_SCOPE = "https://api.fabric.microsoft.com/.default"


def _parse_error_response(response: requests.Response, default_message: str = "Unknown error") -> str:
    """Parse error response from Fabric API, handling various response formats.
    
    Args:
        response: requests.Response object
        default_message: Default message if parsing fails
        
    Returns:
        Parsed error message, truncated if too long
    """
    error_detail = response.text[:ERROR_TEXT_MAX_LENGTH] if len(response.text) > ERROR_TEXT_MAX_LENGTH else response.text
    content_type = response.headers.get("Content-Type", "").lower()
    
    if "application/json" in content_type:
        try:
            body = response.json()
            if isinstance(body, dict):
                error_msg = body.get("error", {})
                if isinstance(error_msg, dict):
                    error_detail = error_msg.get("message", error_detail)
                elif isinstance(error_msg, str):
                    error_detail = error_msg
        except (ValueError, Exception) as e:
            print(f"WARNING: Failed to parse error response: {e}")
            print("         Using raw response text (truncated)")
    
    return error_detail


def _make_fabric_request(
    method: str,
    url: str,
    token: str,
    json_payload: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    operation_description: str = "API request"
) -> requests.Response:
    """Make HTTP request to Fabric API with consistent error handling.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full API URL
        token: Bearer token
        json_payload: Optional JSON payload for POST/PUT requests
        timeout: Request timeout in seconds
        operation_description: Description of the operation for error messages
        
    Returns:
        requests.Response object
        
    Raises:
        Exception: If request fails due to timeout or network error
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_payload,
            timeout=timeout
        )
        return response
    except requests.exceptions.Timeout as e:
        raise Exception(f"Request to Fabric API timed out while {operation_description}") from e
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during {operation_description}: {e}") from e


def get_access_token(token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> str:
    """Get Fabric API access token from credential.
    
    Args:
        token_credential: Azure credential for authentication
        
    Returns:
        Bearer token string
        
    Raises:
        Exception: If token acquisition fails
    """
    try:
        token = token_credential.get_token(FABRIC_TOKEN_SCOPE)
        return token.token
    except Exception as e:
        raise Exception(f"Failed to acquire access token: {str(e)}")


def check_workspace_exists(workspace_name: str, token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> Optional[str]:
    """Check if a workspace with the given name exists.
    
    Args:
        workspace_name: Name of the workspace to check (e.g., "[D] Fabric Blueprint")
        token_credential: Azure credential for authentication
        
    Returns:
        Workspace ID if exists, None if not found
        
    Raises:
        Exception: If API call fails
    """
    token = get_access_token(token_credential)
    list_url = f"{FABRIC_API_BASE_URL}/v1/workspaces"
    
    response = _make_fabric_request(
        method="GET",
        url=list_url,
        token=token,
        operation_description="checking workspace existence"
    )
    
    if response.status_code != 200:
        error_detail = _parse_error_response(response, "Failed to list workspaces")
        raise Exception(f"Failed to list workspaces. Status: {response.status_code}, Response: {error_detail}")
    
    try:
        workspaces_data = response.json()
    except ValueError as e:
        raise Exception(f"Failed to parse workspace list response as JSON: {str(e)}")
    
    workspaces = workspaces_data.get("value", [])
    for workspace in workspaces:
        if workspace.get("displayName") == workspace_name:
            workspace_id = workspace.get("id")
            print(f"  ✓ Workspace '{workspace_name}' already exists (ID: {workspace_id})")
            return workspace_id
    
    return None


def create_workspace(workspace_name: str, capacity_id: str, token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> str:
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
    if not capacity_id:
        raise Exception(
            "Capacity ID is required to auto-create a Fabric workspace. "
            f"Either manually create a workspace named '{workspace_name}' in Fabric, "
            "or set the appropriate FABRIC_CAPACITY_ID_* secret in GitHub to enable auto-creation."
        )
    
    token = get_access_token(token_credential)
    create_url = f"{FABRIC_API_BASE_URL}/v1/workspaces"
    payload = {
        "displayName": workspace_name,
        "capacityId": capacity_id
    }
    
    print(f"  → Creating workspace '{workspace_name}' with capacity '{capacity_id}'...")
    
    response = _make_fabric_request(
        method="POST",
        url=create_url,
        token=token,
        json_payload=payload,
        timeout=CREATE_WORKSPACE_TIMEOUT,
        operation_description="creating workspace"
    )
    
    if response.status_code == 201:
        try:
            body = response.json()
            workspace_id = body.get("id")
            if not workspace_id:
                raise Exception(
                    "Workspace creation returned HTTP 201 but response did not contain a valid 'id' field. "
                    "Inspect Fabric API response for details."
                )
            print(f"  ✓ Workspace created successfully (ID: {workspace_id})")
            return workspace_id
        except ValueError as parse_error:
            print(f"WARNING: Failed to parse JSON success response: {parse_error}")
            raise Exception("Workspace creation succeeded but failed to parse response")
    elif response.status_code == 400:
        # Safely parse error details
        error_detail = _parse_error_response(response, "Invalid workspace creation request")
        raise Exception(f"Invalid workspace creation request: {error_detail}")
    elif response.status_code == 403:
        raise Exception(
            "Service Principal lacks workspace creation permissions.\n\n"
            "Possible causes:\n"
            "1. Missing tenant setting: In Fabric Admin Portal → Tenant Settings → Developer Settings, "
            "enable 'Service principals can create workspaces, connections, and deployment pipelines'\n"
            "2. Missing capacity admin role: In Azure Portal → Fabric Capacity → Settings → Capacity administrators, "
            "add the Service Principal (by Client ID or Enterprise Application Object ID)"
        )
    elif response.status_code == 404:
        raise Exception(f"Invalid capacity ID '{capacity_id}'. Verify FABRIC_CAPACITY_ID_* secret is correct.")
    else:
        error_detail = _parse_error_response(response, "Workspace creation failed")
        raise Exception(f"Workspace creation failed. Status: {response.status_code}, Response: {error_detail}")


def _assign_workspace_role(
    workspace_id: str,
    principal_id: str,
    principal_type: Literal["ServicePrincipal", "Group"],
    role: str,
    token_credential: Union[ClientSecretCredential, DefaultAzureCredential],
    principal_description: str
) -> None:
    """Internal helper to assign a role to a principal (service principal or group) in a workspace.
    
    Args:
        workspace_id: GUID of the workspace
        principal_id: Azure AD Object ID of the principal
        principal_type: Type of principal ("ServicePrincipal" or "Group")
        role: Role to assign (typically "Admin")
        token_credential: Azure credential for authentication
        principal_description: Human-readable description for logging (e.g., "Service Principal", "Entra ID group")
        
    Raises:
        Exception: If role assignment fails
    """
    if not principal_id:
        if principal_description == "Entra ID group":
            print(f"  ℹ No {principal_description} configured. Skipping role assignment.")
        else:
            print(f"  ⚠ WARNING: {principal_description} ID not set. Skipping role assignment.")
        return
    
    token = get_access_token(token_credential)
    url = f"{FABRIC_API_BASE_URL}/v1/workspaces/{workspace_id}/roleAssignments"
    payload = {
        "principal": {
            "id": principal_id,
            "type": principal_type
        },
        "role": role
    }
    
    print(f"  → Adding {principal_description} as {role} to workspace...")
    
    response = _make_fabric_request(
        method="POST",
        url=url,
        token=token,
        json_payload=payload,
        operation_description=f"assigning {principal_description} role"
    )
    
    if response.status_code in (200, 201):
        print(f"  ✓ {principal_description} added as {role} successfully")
    elif response.status_code == 400:
        error_detail = _parse_error_response(response, f"Invalid {principal_description} role assignment request")
        if "already exists" in error_detail.lower() or "already assigned" in error_detail.lower():
            print(f"  ✓ {principal_description} already has {role} access")
        else:
            raise Exception(f"Invalid {principal_description} role assignment request: {error_detail}")
    elif response.status_code == 409:
        print(f"  ✓ {principal_description} already has {role} access")
    elif response.status_code == 404:
        principal_type_hint = "Service Principal Object ID (not Client ID)" if principal_type == "ServicePrincipal" else "Entra ID group Object ID"
        raise Exception(
            f"Invalid {principal_description} Object ID '{principal_id}'. "
            f"Verify the secret contains a valid {principal_type_hint}. "
            "Find it in Azure Portal → Azure Active Directory."
        )
    else:
        error_detail = _parse_error_response(response, f"{principal_description} role assignment failed")
        raise Exception(f"{principal_description} role assignment failed. Status: {response.status_code}, Response: {error_detail}")


def add_workspace_admin(workspace_id: str, service_principal_object_id: str, token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> None:
    """Add a service principal as admin to a workspace.
    
    Args:
        workspace_id: GUID of the workspace
        service_principal_object_id: Azure AD Object ID of the service principal (NOT Client ID)
        token_credential: Azure credential for authentication
        
    Raises:
        Exception: If role assignment fails
    """
    _assign_workspace_role(
        workspace_id=workspace_id,
        principal_id=service_principal_object_id,
        principal_type="ServicePrincipal",
        role="Admin",
        token_credential=token_credential,
        principal_description="Service Principal"
    )


def add_entra_id_group_admin(workspace_id: str, entra_group_id: str, token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> None:
    """Add an Entra ID (Azure AD) group as admin to a workspace.
    
    Args:
        workspace_id: GUID of the workspace
        entra_group_id: Azure AD Object ID of the Entra ID group
        token_credential: Azure credential for authentication
        
    Raises:
        Exception: If role assignment fails
    """
    _assign_workspace_role(
        workspace_id=workspace_id,
        principal_id=entra_group_id,
        principal_type="Group",
        role="Admin",
        token_credential=token_credential,
        principal_description="Entra ID group"
    )


def ensure_workspace_exists(
    workspace_name: str,
    capacity_id: str,
    service_principal_object_id: str,
    token_credential: Union[ClientSecretCredential, DefaultAzureCredential],
    entra_admin_group_id: Optional[str] = None
) -> str:
    """Ensure workspace exists, creating it if necessary.
    
    This is the main entry point for workspace management. It checks if the workspace
    exists, creates it if needed, and ensures the service principal and Entra ID admin
    group (if configured) have admin access.
    
    Args:
        workspace_name: Display name of the workspace (e.g., "[D] Fabric Blueprint")
        capacity_id: Fabric capacity ID for the environment
        service_principal_object_id: Azure AD Object ID of the deployment service principal
        token_credential: Azure credential for authentication
        entra_admin_group_id: Optional Azure AD Object ID of Entra ID group for admin access
        
    Returns:
        Workspace ID (either existing or newly created)
        
    Raises:
        Exception: If workspace cannot be created or accessed
    """
    try:
        print(f"→ Ensuring workspace '{workspace_name}' exists...")
        
        workspace_id = check_workspace_exists(workspace_name, token_credential)
        
        if workspace_id:
            print(f"  ℹ Workspace already exists, ensuring admin access...")
        else:
            print(f"  ℹ Workspace not found, creating new workspace...")
            workspace_id = create_workspace(workspace_name, capacity_id, token_credential)
        
        # Ensure access for service principal and admin group
        add_workspace_admin(workspace_id, service_principal_object_id, token_credential)
        add_entra_id_group_admin(workspace_id, entra_admin_group_id or "", token_credential)
        
        print(f"  ✓ Workspace '{workspace_name}' is ready for deployment")
        return workspace_id
        
    except Exception as e:
        _print_troubleshooting_hints(str(e))
        raise


def _print_troubleshooting_hints(error_msg: str) -> None:
    """Print contextual troubleshooting hints based on error message.
    
    Args:
        error_msg: Error message to analyze for troubleshooting context
    """
    print(f"\n✗ ERROR: Failed to ensure workspace exists: {error_msg}\n")
    
    if "workspace creation permissions" in error_msg:
        print("TROUBLESHOOTING:")
        print("  1. Fabric Tenant Setting:")
        print("     - Open Fabric Admin Portal (https://app.fabric.microsoft.com/admin-portal)")
        print("     - Navigate to: Tenant Settings → Developer Settings")
        print("     - Enable: 'Service principals can create workspaces, connections, and deployment pipelines'")
        print("  2. Capacity Administrator Assignment:")
        print("     - Open Azure Portal → Your Fabric Capacity → Settings → Capacity administrators")
        print("     - Add the Service Principal by Client ID or Enterprise Application name")
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
