# CI/CD Pipeline for TraderAdmin GUI

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline set up for the TraderAdmin GUI application.

## Overview

The pipeline automates the following processes:

- Running lint and type checks on the frontend code
- Running tests
- Building the application for multiple platforms (Windows, macOS, Linux)
- Packaging the application
- Releasing the application on GitHub when a new tag is pushed

## Workflow Triggers

The CI/CD workflow is triggered by:

1. Pull requests to the `main` branch
2. Pushing tags that start with `v` (e.g., `v1.0.0`, `v2.3.1-beta`)

## CI Process

For every pull request and tag push, the following CI steps are performed:

1. **Code Checkout**: The repository is checked out
2. **Environment Setup**: Go and Node.js are set up with appropriate versions
3. **Wails Installation**: The Wails CLI tool is installed
4. **Dependencies Installation**: Frontend dependencies are installed using `npm ci`
5. **Linting & Type Checking**: ESLint and TypeScript checks are run
6. **Tests**: Frontend tests are executed
7. **Build**: The Wails application is built for the target platform

## Packaging

After the build process, platform-specific packaging is performed:

- **Windows**: Creates a ZIP file containing the `.exe` file
- **macOS**: Creates a ZIP file containing the `.app` bundle
- **Linux**: Creates a `.tar.gz` file containing the executable

## CD Process

When a tag is pushed (e.g., `v1.0.0`), in addition to the CI process:

1. A GitHub Release is automatically created with the tag name
2. The packaged artifacts for each platform are attached to the release
3. A changelog is generated from Git commits since the previous tag
4. Installation instructions are added to the release notes

## Release Scripts

The project includes helper scripts to streamline the release process:

- **Linux/macOS**: `scripts/release.sh`
- **Windows**: `scripts/release.bat`

These scripts:
1. Update version number in package.json
2. Create a git commit with the version change
3. Create a git tag with the version
4. Provide instructions to push the changes and tag

### Using the release scripts

**On Linux/macOS:**
```bash
# Make the script executable (first time only)
chmod +x scripts/release.sh
# Create a new release
./scripts/release.sh 1.2.0
```

**On Windows:**
```powershell
# Create a new release
scripts\release.bat 1.2.0
```

## Manual Steps

The following steps must be done manually:

1. Run the appropriate release script with the new version
2. Push the commit and tag as instructed by the script

## Workflow Configuration

The CI/CD pipeline is configured in the `.github/workflows/gui-ci-cd.yml` file in the repository. 