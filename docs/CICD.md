# CI/CD Process for TraderAdmin

This document describes the Continuous Integration and Continuous Deployment process for the TraderAdmin application.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of two main jobs:
1. **lint-and-build**: Runs on all PRs to main and tag pushes
2. **release**: Only runs on tag pushes and creates GitHub Releases

## Workflow Trigger Events

- **Pull Requests** to the `main` branch
- **Tag Pushes** using the format `v*` (e.g., `v1.0.0`, `v0.1.2`)

## Build Matrix

The application is built on three operating systems simultaneously:
- Windows (windows-latest)
- macOS (macos-latest)
- Linux (ubuntu-latest)

## CI Process (Pull Requests)

When a PR is created against the main branch, the following steps occur:

1. **Code Checkout**: The repository is cloned
2. **Environment Setup**: Go, Node.js, and Wails are installed
3. **Frontend Validation**:
   - `npm ci` installs dependencies
   - `npm run lint` checks for code style issues
   - `npm run check` validates TypeScript
4. **Application Build**: The full application is built with Wails
5. **Artifact Upload**: Build artifacts are uploaded but not released

This ensures that every PR can successfully build across all platforms before merging.

## CD Process (Tags)

When a tag with the `v*` pattern is pushed, the following additional steps occur:

1. All steps from the CI process are executed
2. **Release Creation**: A GitHub Release is created with the tag name
3. **Asset Attachment**: The built binaries for all platforms are attached:
   - Windows: `TraderAdmin-windows.zip`
   - macOS: `TraderAdmin-macos.zip`
   - Linux: `TraderAdmin-linux.tar.gz`

## Manual Deployment

You can trigger a release by pushing a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Customizing the Process

To modify the CI/CD process, edit the `.github/workflows/gui-ci-cd.yml` file. Common customizations include:

- Adding code coverage reporting
- Implementing automatic version number increments
- Configuring notification services (Slack, Email, etc.)
- Adding additional test steps

## Troubleshooting

Check the GitHub Actions tab in your repository to see build logs. Common issues include:

- Missing dependencies in the workflow environment
- Failing linting or type checks
- Build failures on specific platforms 