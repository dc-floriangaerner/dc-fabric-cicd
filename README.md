# fabric-cicd

Demonstration project for setting up CI/CD with GitHub Actions for Microsoft Fabric using MCP servers.

## Overview

This project demonstrates how to:
- Use Microsoft Fabric MCP Server for Fabric operations
- Use Azure MCP Server for Azure resource management
- Integrate `fabric-cicd` and `fabric-cli` Python libraries
- Set up CI/CD pipelines with GitHub Actions

## Prerequisites

- Python 3.8 or higher
- Node.js (for MCP servers via npx)
- Azure/Fabric credentials for authentication

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or using the modern approach:

```bash
pip install -e .
```

For development with additional tools:

```bash
pip install -e ".[dev]"
```

### 2. Configure MCP Servers

The project includes MCP server configuration in `.mcp/config.json`. To use the MCP servers, you'll need to set the following environment variables:

#### For Fabric MCP Server:
```bash
export FABRIC_TENANT_ID="your-tenant-id"
export FABRIC_CLIENT_ID="your-client-id"
export FABRIC_CLIENT_SECRET="your-client-secret"
```

#### For Azure MCP Server:
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

### 3. Using MCP Servers

The MCP servers are configured to run via npx, which means they'll be automatically downloaded and executed when needed. The configuration file `.mcp/config.json` defines:

- **Fabric MCP Server** (`@microsoft/mcp-server-fabric`): Provides tools for working with Microsoft Fabric
- **Azure MCP Server** (`@azure/mcp-server-azure`): Provides tools for Azure resource management

## Project Structure

```
fabric-cicd/
├── .mcp/
│   └── config.json          # MCP server configuration
├── .github/
│   └── workflows/           # GitHub Actions workflows (see below)
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Python project configuration
├── .gitignore               # Git ignore patterns
└── README.md                # This file
```

## Python Libraries

This project uses the following Python libraries:

- **fabric-cicd**: Core library for Fabric CI/CD operations
- **fabric-cli**: Command-line interface for Fabric operations
- **azure-identity**: Azure authentication library
- **azure-core**: Azure SDK core library

## GitHub Actions CI/CD

To set up GitHub Actions for CI/CD, create workflow files in `.github/workflows/`. Examples:

### Basic CI Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest
```

### Fabric Deployment Workflow

Create `.github/workflows/deploy-fabric.yml`:

```yaml
name: Deploy to Fabric

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Deploy to Fabric
        env:
          FABRIC_TENANT_ID: ${{ secrets.FABRIC_TENANT_ID }}
          FABRIC_CLIENT_ID: ${{ secrets.FABRIC_CLIENT_ID }}
          FABRIC_CLIENT_SECRET: ${{ secrets.FABRIC_CLIENT_SECRET }}
        run: |
          # Add your Fabric deployment commands here
          fabric-cli deploy
```

## Environment Variables for GitHub Actions

To use the workflows with MCP servers and Fabric, add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `FABRIC_TENANT_ID`
   - `FABRIC_CLIENT_ID`
   - `FABRIC_CLIENT_SECRET`
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
   - `AZURE_SUBSCRIPTION_ID`

## Usage Examples

### Using fabric-cli

```bash
# List Fabric workspaces
fabric-cli workspace list

# Deploy to Fabric
fabric-cli deploy --workspace-id <workspace-id>
```

### Using fabric-cicd programmatically

```python
from fabric_cicd import FabricClient

# Initialize client
client = FabricClient(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Perform operations
workspaces = client.list_workspaces()
```

## Contributing

Contributions are welcome! Please ensure that:

1. Code follows Python best practices
2. Tests are included for new features
3. Documentation is updated accordingly

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Additional Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [MCP Server Documentation](https://github.com/microsoft/mcp)