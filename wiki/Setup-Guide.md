# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for multi-workspace Fabric deployments.

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Azure AD (Entra ID) tenant access to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Dev, Test, and Prod Fabric workspaces created for each workspace folder

## Step 1: Create Azure Service Principal

### Using Azure Portal

1. Navigate to **Microsoft Entra ID** → **App registrations**
2. Click **New registration**
3. Name: `fabric-cicd-deployment`
4. Click **Register**
5. Copy the **Application (client) ID** (this is `AZURE_CLIENT_ID`)
6. Copy the **Directory (tenant) ID** (this is `AZURE_TENANT_ID`)
7. Go to **Certificates & secrets** → **New client secret**
8. Add description: `GitHub Actions`
9. Copy the **secret value** (this is `AZURE_CLIENT_SECRET`)

### Using Azure CLI

```bash
# Login to Azure
az login

# Create Service Principal
SP_OUTPUT=$(az ad sp create-for-rbac --name "fabric-cicd-deployment" --skip-assignment)

# Extract values
echo "AZURE_CLIENT_ID:" $(echo $SP_OUTPUT | jq -r '.clientId')
echo "AZURE_CLIENT_SECRET:" $(echo $SP_OUTPUT | jq -r '.clientSecret')
echo "AZURE_TENANT_ID:" $(echo $SP_OUTPUT | jq -r '.tenantId')

# Get Object ID for the Service Principal
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
OBJECT_ID=$(az ad sp show --id $CLIENT_ID --query id -o tsv)
echo "DEPLOYMENT_SP_OBJECT_ID: $OBJECT_ID"
```

## Step 2: Grant Fabric Workspace Permissions

For **each workspace** in **each environment** (Dev, Test, Prod):

1. Open the workspace in Fabric portal
2. Click **Workspace settings** → **Manage access**
3. Click **Add people or groups**
4. Search for your Service Principal name (`fabric-cicd-deployment`)
5. Assign role: **Admin** or **Contributor**
6. Click **Add**

## Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

### Required Secrets

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration → Overview |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration → Overview |

### Optional Secrets (For Auto-Creation)

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `FABRIC_CAPACITY_ID_DEV` | Dev Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `FABRIC_CAPACITY_ID_TEST` | Test Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `FABRIC_CAPACITY_ID_PROD` | Prod Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `DEPLOYMENT_SP_OBJECT_ID` | Service Principal Object ID | Azure AD → Enterprise Applications |
| `FABRIC_ADMIN_GROUP_ID` | Entra ID group for admin access | Azure AD → Groups → Object ID |

## Step 4: Test the Pipeline

### Test Dev Deployment (Automatic)

1. Create a test change in a workspace:
```bash
git checkout -b feature/test-deployment
echo "# Test" >> workspaces/"Fabric Blueprint"/test.md
git add workspaces/"Fabric Blueprint"/test.md
git commit -m "test: verify CI/CD pipeline"
git push origin feature/test-deployment
```

2. Create Pull Request to `main`
3. Merge the PR
4. Watch the **Actions** tab for automatic deployment to Dev

### Test Manual Deployment to Test/Production

1. Go to **Actions** → **Deploy to Microsoft Fabric**
2. Click **Run workflow**
3. Select environment (**test** or **prod**)
4. Click **Run workflow** button
5. Monitor the deployment in the Actions tab

## Next Steps

- Configure [Workspace Configuration](Workspace-Configuration) for your workspaces
- Review the [Deployment Workflow](Deployment-Workflow) to understand the deployment process
- Check [Troubleshooting](Troubleshooting) for common issues

## Resources

- [Full Setup Documentation (SETUP.md)](https://github.com/dc-floriangaerner/fabric-cicd/blob/main/SETUP.md)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
