# Fabric CI/CD Reference Architecture Wiki

Welcome to the Fabric CI/CD Reference Architecture documentation!

## Quick Links

- [Setup Guide](Setup-Guide)
- [Workspace Configuration](Workspace-Configuration)
- [Deployment Workflow](Deployment-Workflow)
- [Troubleshooting](Troubleshooting)

## Overview

This wiki provides comprehensive documentation for implementing CI/CD pipelines for Microsoft Fabric workspaces using GitHub Actions and the `fabric-cicd` Python library.

### Key Features

- **Multi-Workspace Support**: Deploy multiple Fabric workspaces from a single repository
- **Automatic Workspace Creation**: Auto-create workspaces if they don't exist (optional)
- **Medallion Architecture**: Bronze → Silver → Gold data layers
- **Multi-stage Deployment**: Dev → Test → Production with approval gates
- **Git-based Deployment**: Single source of truth in `main` branch

## Getting Started

New to this project? Start with the [Setup Guide](Setup-Guide) to configure your CI/CD pipeline.

## Repository Structure

```
workspaces/
├── Fabric Blueprint/
│   ├── config.yml              # Workspace deployment configuration
│   ├── parameter.yml           # ID transformation rules
│   ├── 1_Bronze/              # Raw data ingestion
│   ├── 2_Silver/              # Transformed/cleansed data
│   ├── 3_Gold/                # Business-ready analytics
│   └── 4_Analytics/           # Semantic models, reports, agents
```

## Contributing

See the main [README](https://github.com/dc-floriangaerner/fabric-cicd/blob/main/README.md) for contribution guidelines.

## Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [fabric-cicd Library](https://pypi.org/project/fabric-cicd/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
