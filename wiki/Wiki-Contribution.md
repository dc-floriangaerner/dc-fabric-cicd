# Wiki Contribution Guide

This guide explains how to contribute to the Fabric CI/CD wiki documentation.

## Overview

This directory contains the markdown files that are automatically synced to the [GitHub Wiki](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki).

## How It Works

1. **Edit** markdown files in this `/wiki` folder
2. **Commit** changes to a feature branch
3. **Create PR** to `main` branch
4. **Merge PR** - Wiki is automatically synced via GitHub Actions

## Automatic Sync

When changes to files in this directory are pushed to the `main` branch, the `.github/workflows/sync-wiki.yml` workflow automatically:
- Clones the wiki repository (`https://github.com/dc-floriangaerner/fabric-cicd.wiki.git`)
- Copies all markdown files from `/wiki` to the wiki repository
- Commits and pushes the changes to the wiki

## Wiki Pages

| File | Wiki Page | Description |
|------|-----------|-------------|
| `Home.md` | [Home](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Home) | Wiki home page with overview |
| `Setup-Guide.md` | [Setup Guide](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Setup-Guide) | Step-by-step setup instructions |
| `Workspace-Configuration.md` | [Workspace Configuration](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Workspace-Configuration) | Configure workspaces with config.yml and parameter.yml |
| `Deployment-Workflow.md` | [Deployment Workflow](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Deployment-Workflow) | Understand the CI/CD pipeline |
| `Troubleshooting.md` | [Troubleshooting](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Troubleshooting) | Common issues and solutions |
| `Wiki-Contribution.md` | [Wiki Contribution](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Wiki-Contribution) | Guide for contributing to wiki |

## Adding New Wiki Pages

1. Create a new markdown file in this directory (e.g., `New-Page.md`)
2. Add content following markdown syntax
3. Link to it from other pages using: `[Link Text](New-Page)`
4. Commit and push to `main` to sync

## Wiki Naming Conventions

- Use **PascalCase** with hyphens for file names: `New-Page.md`
- This matches GitHub Wiki URL structure: `/wiki/New-Page`
- The `.md` extension is automatically removed in wiki URLs
- Spaces in file names become hyphens in URLs

## Manual Sync

If you need to manually trigger the wiki sync:
1. Go to **Actions** tab
2. Select **Sync Wiki** workflow
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow** button

## Benefits of This Approach

- **Version Control**: Wiki content is version controlled alongside code
- **Pull Request Review**: Documentation changes go through PR review process
- **Sync with Code**: Documentation stays in sync with code changes
- **Single Source of Truth**: Main repository is the source for all content
- **Collaboration**: Multiple contributors can work on documentation simultaneously

## Questions or Feedback

For questions about contributing to the wiki or feedback on documentation, contact [florian.gaerner@dataciders.com](mailto:florian.gaerner@dataciders.com)

## References

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
