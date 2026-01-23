# Copilot Instructions for Fabric CI/CD Reference Architecture

## Project Overview

This is a **reference architecture** for Microsoft Fabric CI/CD using a **medallion architecture** (Bronze → Silver → Gold) for data engineering. The codebase defines Fabric workspace items as code, enabling Git-based version control, collaboration, and automated deployment workflows.

**Key Purpose**: Serve as a company-wide template for Fabric projects following Microsoft best practices for lifecycle management.

## Git Integration & CI/CD Strategy

### Workspace-to-Git Mapping

This project follows **Fabric Git Integration** patterns where:
- **Private development workspaces only** are connected to Git (feature branches)
- **Dev, Test, Prod workspaces** are NOT connected to Git - they receive deployments via CI/CD pipelines
- Developers use isolated workspaces connected to their feature branches for development

### Supported Git Providers

- **GitHub** (including GitHub Enterprise)

### Branch Strategy

**Trunk-based development** workflow:
- **main**: Single source of truth for all deployments
- **feature/***: Short-lived feature branches that merge to main
- **Private dev branches**: Individual developer branches for isolated work

### Deployment Approach: Git-based with Build Environments

This architecture uses **Git-based deployments with Build environments** for configuration transformation between stages.

**Why Git-based with Build Environments**
- Single source of truth in `main` branch (trunk-based workflow)
- Build environments allow modification of workspace-specific attributes (connectionId, lakehouseId, parameters)
- Custom scripts can adjust configurations for each stage (Dev/Test/Prod)
- Uses `fabric-cicd` library for deploying items programmatically

**Deployment Flow:**

1. **PR merged to main** → Triggers build pipeline
2. **Build Pipeline** (per stage: Dev → Test → Prod):
   - Spin up Build environment
   - Run unit tests
   - Execute configuration scripts to modify item definitions for target stage
   - Adjust connections, data sources, parameters
3. **Release Pipeline**:
   - Use `fabric-cicd` library to deploy items to workspace
   - Run post-deployment ingestion/configuration tasks
4. **Approval Gates**: Release managers approve progression between stages

**Deployment Tool:**
- `fabric-cicd` library: Handles deployment of modified item content to workspaces

### Best Practices for This Architecture

- **Separate workspaces per stage**: Dev, Test, Prod workspaces with different capacities
- **Parameterize everything**: All stage-specific configs (connections, lakehouse IDs, data sources) must be parameterizable
- **Build scripts**: Maintain transformation scripts in repo for modifying item definitions
- **Small, frequent merges to main**: Keep feature branches short-lived
- **Commit related changes together**: Group changes that must deploy atomically
- **Private development branches**: Each developer works in isolated branch/workspace
- **Pull request workflow**: All changes to main require PR approval
- **Configuration as code**: Store stage-specific configs (Dev/Test/Prod) in repo

## Fabric MCP Server Integration

**When working with Microsoft Fabric tasks, always prefer using the Fabric MCP server.**

The Fabric MCP (Model Context Protocol) server provides specialized tools and context for:
- Querying Fabric workspaces, items, and metadata
- Managing OneLake files, directories, and shortcuts
- Accessing Fabric API specifications and best practices
- Working with Fabric item definitions (notebooks, lakehouses, pipelines, semantic models)
- Retrieving official Microsoft Fabric documentation

**Use the Fabric MCP server for:**
- Creating or modifying Fabric workspace items
- Querying workspace structure and item relationships
- Understanding Fabric API patterns and schemas
- Getting context-aware Fabric best practices
- Working with OneLake storage operations

**Benefits:**
- Access to latest Fabric API specifications
- Context-aware guidance for Fabric-specific tasks
- Direct integration with Fabric REST APIs
- Official Microsoft documentation and examples

## Architecture

### Medallion Layers

1. **Bronze Layer** (`1_Bronze/`): Raw data ingestion
   - `lakehouse_bronze.Lakehouse/`: Source data storage
   - `ingestion/cp_br_source.CopyJob/`: Data pipeline copy jobs (batch mode)

2. **Silver Layer** (`2_Silver/`): Transformed/cleansed data
   - `lakehouse_silver.Lakehouse/`: Cleaned data storage
   - `transformation/nb_sl_transform.Notebook/`: PySpark transformation notebooks

3. **Gold Layer** (`3_Gold/`): Business-ready analytics
   - `lakehouse_gold.Lakehouse/`: Aggregated/modeled data
   - `modeling/nb_gd_modeling.Notebook/`: Data modeling notebooks

4. **Analytics** (`4_Analytics/`): Semantic models, reports, and agents
   - Semantic models: Power BI semantic models for analytics
   - Reports: Power BI reports and dashboards
   - `Data Agents/da_agent.DataAgent/`: AI agent definitions (schema: 2.1.0)
   - `env.Environment/`: Workspace environment settings

## File Structure Conventions

### Fabric Item Structure

Each Fabric item follows this pattern:
```
<item-name>.<ItemType>/
  ├── <item-type>-content.json/py  # Main definition
  ├── <item-type>.metadata.json    # Item metadata
  ├── alm.settings.json            # ALM/deployment config (for lakehouses)
  └── shortcuts.metadata.json      # OneLake shortcuts (for lakehouses)
```

### Key File Types

- **Notebooks**: `notebook-content.py` with inline `# METADATA` blocks
  - Kernel: `synapse_pyspark`
  - Structure: Python source with META comments for cell boundaries
  
- **Copy Jobs**: `copyjob-content.json` with `properties.jobMode` (typically "Batch")

- **Lakehouses**: 
  - `lakehouse.metadata.json`: Schema config (`{"defaultSchema":"dbo"}`)
  - `alm.settings.json`: Controls ALM for shortcuts, data access roles
  - `shortcuts.metadata.json`: OneLake/ADLS/S3/Dataverse shortcuts

- **Environments**: `Sparkcompute.yml` for cluster config
  - Runtime version 2.0
  - Driver/executor cores and memory settings
  - Dynamic executor allocation enabled

- **Data Agents**: `data_agent.json` follows schema `2.1.0` from Microsoft

## Development Workflow

### Naming Conventions

**Item Prefixes**:
- `cp_`: Copy jobs (data pipelines)
- `nb_`: Notebooks (PySpark/Python)
- `lakehouse_`: Lakehouse data stores
- `da_`: Data agents

**Layer Prefixes**:
- `br_`: Bronze layer (raw ingestion)
- `sl_`: Silver layer (transformation)
- `gd_`: Gold layer (modeling/analytics)

**Restrictions** (from Microsoft Fabric):
- Display names: Max 256 characters
- Cannot end with `.` or space
- Forbidden characters: `" / : < > \ * ? |`
- Branch names: Max 244 characters
- File paths: Max 250 characters
- Max file size: 25 MB
- Folder depth: Max 10 levels

### Working with Fabric Items

- **Isolated development**: Use private workspace or feature branch per developer
- **Folder structure**: Workspace folders sync to Git repo folders (empty folders ignored)
- **Workspace limit**: Max 1,000 items per workspace
- **Version control**: Always commit related changes together for atomic deployments

### Notebook Development

Fabric notebooks use special comment syntax:
```python
# METADATA ********************
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {}
# META }
# CELL ********************
# Your code here
```

Always preserve this structure when editing notebooks.

### ALM Settings

The `alm.settings.json` version `1.0.1` controls deployment behavior:
- **Shortcuts**: Can enable/disable OneLake, ADLS Gen2, Dataverse, S3, GCS shortcuts
- **DataAccessRoles**: Typically disabled in CI/CD scenarios

## Spark Configuration

Environment Spark settings (`Sparkcompute.yml`):
- **Native execution engine**: Enabled
- **Driver**: 8 cores, 56GB memory
- **Executors**: 8 cores, 56GB memory, dynamic allocation (1 min, 1 max)
- **Runtime**: Version 2.0

## Git Integration

This is a Git-based deployment model where:
- Each Fabric workspace item is a directory
- Changes are version controlled
- Structure mirrors Fabric workspace organization

### Git Status States

Items in workspace show Git status:
- **Synced**: Item matches Git branch
- **Conflict**: Changed in both workspace and Git
- **Uncommitted changes**: Workspace ahead of Git
- **Update required**: Git ahead of workspace
- **Unsupported item**: Item type not supported in Git

### Commit and Update Rules

- **Commit**: Push workspace changes to Git (can select specific items)
- **Update**: Pull Git changes to workspace (always full branch update)
- **Conflicts**: Must be resolved before update can proceed
- **Direction**: Can only sync one direction at a time

When creating new items, follow the exact folder/file naming patterns observed in existing items.

## Common Tasks

### Adding a New Lakehouse
1. Create `<name>.Lakehouse/` directory in appropriate layer
2. Add `lakehouse.metadata.json` with `{"defaultSchema":"dbo"}`
3. Add `alm.settings.json` (copy from existing lakehouse)
4. Add empty `shortcuts.metadata.json` (`[]`)
5. **Important**: Lakehouse IDs must be transformed by build scripts for each environment

### Adding a New Notebook
1. Create `<name>.Notebook/` directory
2. Add `notebook-content.py` with proper METADATA structure
3. Use `synapse_pyspark` kernel
4. Include cell boundaries with `# CELL` comments
5. **Important**: Parameterize any lakehouse references or connections

### Adding a Copy Job
1. Create `<name>.CopyJob/` directory
2. Add `copyjob-content.json` with `properties.jobMode`
3. Define `activities` array for pipeline steps
4. **Important**: Connection IDs and data source paths must be parameterized for build transformation

### Build Pipeline Configuration (Future Implementation)

Build scripts should handle:
- **Connection transformations**: Replace connection IDs for target environment
- **Lakehouse ID substitution**: Update lakehouse references in notebooks, pipelines
- **Parameter updates**: Environment-specific values (data source URLs, storage paths)
- **Item relationships**: Adjust logical IDs for cross-item references

### CI/CD Pipeline Structure (Future Implementation)

```
.github/workflows/ or .azure-pipelines/
├── build-dev.yml        # Build & deploy to Dev
├── build-test.yml       # Build & deploy to Test  
├── build-prod.yml       # Build & deploy to Prod
└── scripts/
    ├── transform-config.ps1   # Configuration transformation
    └── deploy-items.ps1       # Fabric API deployment
```
