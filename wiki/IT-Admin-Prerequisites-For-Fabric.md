# IT Admin Prerequisites for Fabric

This page is a handoff for IT administrators.

It describes only:

- what IT needs to create
- what IT needs to provide to the project team
- why each item is required

## Name Mapping

The project uses GitHub secret names.
The Azure portal uses different labels.

| Azure / Entra portal label | Project / GitHub secret name | Notes |
|---|---|---|
| Application (client) ID | `AZURE_CLIENT_ID` | from the App Registration / Service Principal |
| Directory (tenant) ID | `AZURE_TENANT_ID` | tenant identifier in Microsoft Entra ID |
| Client secret Value | `AZURE_CLIENT_SECRET` | use the secret value, not the secret ID |
| Subscription ID | `ARM_SUBSCRIPTION_ID` | Azure subscription hosting the Terraform state storage |
| Group Object ID | `entra_admin_group_object_id` | Object ID of the Entra admin security group |

## What IT Needs To Create

### 1. One CI/CD Service Principal

Please create one Microsoft Entra ID application / Service Principal for this solution.

Please provide back to the project team:

- Application (client) ID -> `AZURE_CLIENT_ID`
- Client secret Value -> `AZURE_CLIENT_SECRET`
- Directory (tenant) ID -> `AZURE_TENANT_ID`

Why this is needed:

- the deployment pipelines authenticate non-interactively
- the same identity is used to provision Fabric workspaces and deploy content into them
- the same identity is also used for the optional feature workspace automation

### 2. One Entra ID Admin Group

Please create one Entra ID security group for workspace administration.

Please provide back to the project team:

- the group Object ID as `entra_admin_group_object_id`

Why this is needed:

- the group is assigned as `Admin` on the Fabric workspaces
- this gives named human administrators access independent of the CI/CD identity
- this provides operational support and break-glass access when manual intervention is needed

Note:

- the `Admin` role assignment is applied automatically during provisioning
- IT only needs to create the group and provide its Object ID

### 3. Fabric Capacity Assignment

Please create or provide a Fabric capacity in Azure for each environment:

- Dev
- Test
- Prod

Please provide back to the project team:

- the capacity ID for Dev
- the capacity ID for Test
- the capacity ID for Prod
- the capacity names used for Dev, Test, and Prod

Why this is needed:

- each Fabric workspace must be attached to a capacity
- the environments are deployed separately, so each stage needs a valid target capacity

How to set this up:

- create the required Microsoft Fabric capacities in Azure
- add the Entra admin group as a capacity administrator
- add the CI/CD Service Principal as a capacity administrator

Why the capacity administrator assignment is needed:

- the Entra admin group needs administrative access to the capacity
- the CI/CD Service Principal needs to be able to use the capacity for workspace provisioning and workspace assignment

Important guidance:

- the same capacity can be reused across multiple stages if needed
- it is highly recommended to use a dedicated capacity for Production
- a dedicated Production capacity reduces the risk of non-production workloads affecting business-critical workloads

### 4. Azure Storage for Terraform State

In this project, Terraform is used to:

- create the Fabric workspaces
- assign each workspace to the configured Fabric capacity
- assign the Entra admin group as `Admin` on each workspace
- keep those infrastructure changes managed and repeatable across environments

Please create or provide Azure Blob Storage for Terraform state.

Current default naming in this repository:

- Resource Group: `rg-fabric-cicd-tfstate`
- Storage Account: `stsfabriccicdtfstate`
- Container: `tfstate`

Please provide back to the project team:

- the Azure subscription ID as `ARM_SUBSCRIPTION_ID`
- confirmation of the storage account details if different from the defaults

Why this is needed:

- Terraform stores its state in Azure Blob Storage
- without state storage, infrastructure changes cannot be tracked or applied safely

### 5. Fabric Admin Portal Settings

Please enable the following settings in the Fabric Admin Portal.

| Fabric Admin Portal setting | Minimum scope to enable |
|---|---|
| Users can create Fabric items | Entra admin group at minimum |
| Create workspaces | Entra admin group at minimum |
| Use semantic models accross workspaces | Entire organization |
| Service principals can create workspaces, connections, and deployment pipelines | CI/CD Service Principal at minimum |
| Service principals can call Fabric public APIs | CI/CD Service Principal at minimum |
| Users can synchronize workspace items with their Git repositories | Entire organization |
| Users can sync workspace items with GitHub repositories | Entire organization |

Why this is needed:

- these settings allow the required Fabric automation and Git integration to work
- the Service Principal based deployment flow depends on the service-principal-specific settings being enabled
- workspace and Git features depend on the corresponding tenant settings being enabled

## What Permissions IT Needs To Grant

### 1. Permission for the CI/CD Service Principal on Azure Storage

Please grant this Azure role:

- `Storage Blob Data Contributor`

Scope:

- on the Azure Storage Account used for Terraform state

Why this is needed:

- Terraform must be able to read and write its state file in Blob Storage

## What IT Needs To Send Back

Please send the following values to the project team:

| Item | What IT provides |
|---|---|
| Service Principal | Application (client) ID, Client secret Value, Directory (tenant) ID |
| Entra admin group | Object ID |
| Dev capacity | capacity ID and capacity name |
| Test capacity | capacity ID and capacity name |
| Prod capacity | capacity ID and capacity name |
| Azure subscription | Subscription ID |
| Terraform state storage | actual storage naming if different from the default |

## Optional Only: Feature Workspace Setup

This section is only needed if feature branch workspaces should be automated.

### 1. Feature Workspace Capacity

Please provide one additional Fabric capacity ID for feature workspaces.

Why this is needed:

- temporary feature workspaces also need a valid capacity assignment

### 2. Fabric Git Connection

Please create or provide an existing Fabric Git connection for the GitHub repository.

Please provide back to the project team:

- the connection name or connection ID

Why this is needed:

- the optional feature workspace automation connects Fabric workspaces to GitHub
- without this connection, feature workspace creation cannot complete

### 3. Access for the CI/CD Service Principal to Use the Git Connection

Please ensure the CI/CD Service Principal can use the configured Fabric Git connection.

Why this is needed:

- the feature workspace automation uses the Service Principal to connect and initialize those workspaces from Git

## Short Request Summary

If a very short IT request is needed, this is the minimum ask:

1. Create one Service Principal and provide:
   Application (client) ID, Client secret Value, Directory (tenant) ID
2. Create one Entra admin group and provide:
   `entra_admin_group_object_id`
3. Provide Fabric capacity IDs for:
   Dev, Test, Prod
4. Create or provide Azure Blob Storage for Terraform state and provide:
   Subscription ID
5. Add the Entra admin group and the CI/CD Service Principal as capacity administrators on the Fabric capacities
6. Grant the Service Principal:
   `Storage Blob Data Contributor` on the Terraform state storage account
7. Enable the required Fabric Admin Portal settings for workspace creation, public APIs, and Git integration
8. Optional only for feature workspaces:
   provide a feature capacity and a Fabric Git connection
