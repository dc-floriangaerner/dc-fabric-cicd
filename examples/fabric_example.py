"""
Example script demonstrating how to use fabric-cicd and fabric-cli libraries.

This script shows basic operations with Microsoft Fabric using the Python libraries.
"""

import os
from typing import Optional


def get_env_variable(var_name: str) -> Optional[str]:
    """Get environment variable with a helpful error message if not found."""
    value = os.getenv(var_name)
    if not value:
        print(f"Warning: {var_name} not set in environment variables")
    return value


def main():
    """Main function to demonstrate Fabric operations."""
    
    print("=" * 60)
    print("Microsoft Fabric CI/CD Example")
    print("=" * 60)
    print()
    
    # Load environment variables
    tenant_id = get_env_variable("FABRIC_TENANT_ID")
    client_id = get_env_variable("FABRIC_CLIENT_ID")
    client_secret = get_env_variable("FABRIC_CLIENT_SECRET")
    
    if not all([tenant_id, client_id, client_secret]):
        print()
        print("Error: Missing required environment variables.")
        print("Please set FABRIC_TENANT_ID, FABRIC_CLIENT_ID, and FABRIC_CLIENT_SECRET")
        print()
        print("You can:")
        print("1. Copy .env.template to .env and fill in your credentials")
        print("2. Source the .env file: source .env")
        print("3. Or export the variables manually")
        return
    
    print("Environment variables loaded successfully!")
    print()
    
    # Example: Initialize Fabric client
    # Uncomment and modify based on actual fabric-cicd API
    """
    from fabric_cicd import FabricClient
    
    client = FabricClient(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # List workspaces
    print("Fetching Fabric workspaces...")
    workspaces = client.list_workspaces()
    
    print(f"Found {len(workspaces)} workspace(s):")
    for workspace in workspaces:
        print(f"  - {workspace.name} (ID: {workspace.id})")
    
    print()
    print("Example completed successfully!")
    """
    
    print("Note: This is a template example.")
    print("Uncomment the code above and adjust based on the actual")
    print("fabric-cicd library API to perform real operations.")
    print()


if __name__ == "__main__":
    main()
