# MCP Server Configuration

This directory contains the configuration for Model Context Protocol (MCP) servers used in this project.

## What are MCP Servers?

MCP (Model Context Protocol) servers provide standardized interfaces for AI assistants to interact with external services and tools. This project uses MCP servers to enable seamless integration with Microsoft Fabric and Azure.

## Available Servers

### 1. Fabric MCP Server (`@microsoft/mcp-server-fabric`)

Provides tools and capabilities for working with Microsoft Fabric:
- Workspace management
- Dataset operations
- Report management
- Pipeline orchestration
- Fabric resource deployment

**Required Environment Variables:**
- `FABRIC_TENANT_ID`: Your Azure AD tenant ID
- `FABRIC_CLIENT_ID`: Application (client) ID for authentication
- `FABRIC_CLIENT_SECRET`: Client secret for authentication

### 2. Azure MCP Server (`@azure/mcp-server-azure`)

Provides tools and capabilities for Azure resource management:
- Resource group operations
- Storage account management
- Key Vault access
- Azure resource deployment
- Subscription management

**Required Environment Variables:**
- `AZURE_TENANT_ID`: Your Azure AD tenant ID
- `AZURE_CLIENT_ID`: Application (client) ID for authentication
- `AZURE_CLIENT_SECRET`: Client secret for authentication
- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

## Configuration File

The `config.json` file defines how MCP servers are started and configured. Each server configuration includes:

- **command**: The executable to run (typically `npx` for Node.js packages)
- **args**: Arguments passed to the command
- **env**: Environment variables required by the server

## Usage

### For Development

When using an AI assistant or IDE that supports MCP:

1. Ensure environment variables are set in your shell or `.env` file
2. The AI assistant will automatically use the MCP servers defined in `config.json`
3. No additional setup is required - servers are started on-demand

### For CI/CD (GitHub Actions)

In your GitHub Actions workflows:

1. Set the required secrets in your repository settings
2. The workflow will automatically use these secrets as environment variables
3. MCP servers can be used during deployment and automation tasks

Example in workflow:

```yaml
env:
  FABRIC_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
  FABRIC_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
  FABRIC_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
```

## Setting Up Credentials

### 1. Create Azure AD App Registration

```bash
# Using Azure CLI
az ad app create --display-name "fabric-cicd-app"

# Note the appId (client ID) and tenant ID
```

### 2. Create Client Secret

```bash
# Create a client secret
az ad app credential reset --id <app-id>

# Note the client secret (password)
```

### 3. Grant Permissions

Grant the necessary permissions to your app registration:
- For Fabric: Fabric API permissions
- For Azure: Appropriate Azure RBAC roles (e.g., Contributor)

### 4. Set Environment Variables

Create a `.env` file in the project root:

```bash
cp ../.env.template ../.env
# Edit .env with your credentials
```

Or export them directly:

```bash
export FABRIC_TENANT_ID="your-tenant-id"
export FABRIC_CLIENT_ID="your-client-id"
export FABRIC_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

## Troubleshooting

### Server Not Starting

1. Check that Node.js is installed: `node --version`
2. Verify environment variables are set: `echo $FABRIC_TENANT_ID`
3. Check network connectivity to Azure/Fabric services

### Authentication Errors

1. Verify credentials are correct
2. Check that the service principal has appropriate permissions
3. Ensure the tenant ID matches your Azure AD tenant

### MCP Server Updates

MCP servers are automatically downloaded via `npx -y`, which always uses the latest version. To pin to a specific version, modify the args in `config.json`:

```json
"args": [
  "-y",
  "@microsoft/mcp-server-fabric@1.0.0"
]
```

## Additional Resources

- [MCP Protocol Documentation](https://github.com/anthropics/mcp)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Azure Documentation](https://learn.microsoft.com/azure/)
