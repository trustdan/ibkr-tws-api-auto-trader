# 07-gui-ci-cd.md

## 1. Overview

This document defines the CI/CD pipeline for the Wails GUI. We will:

* **Lint & Build**: run Svelte linting, TypeScript checks, and build desktop binaries for Windows, macOS, and Linux
* **Package**: produce installer artifacts (binaries, NSIS installer)
* **Publish Artifacts**: upload build artifacts to GitHub Releases

By automating GUI builds, we ensure consistent, cross-platform delivery with minimal manual steps.

## 2. GitHub Actions Workflow

Create `.github/workflows/gui-ci-cd.yml`:

```yaml
name: GUI CI/CD

on:
  pull_request:
    branches: [ main ]
  push:
    tags: [ 'v*' ]

jobs:
  lint-and-build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Lint and Type Check
        run: |
          cd frontend
          npm run lint
          npm run check
      - name: Build Wails App
        run: |
          cd backend
          go build -o trader-admin
          cd ../frontend
          npm run build
          cd ..
          wails build
      - name: Archive Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: TraderAdmin-${{ matrix.os }}
          path: build/bin

  release:
    if: startsWith(github.ref, 'refs/tags/')
    needs: lint-and-build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Download build artifacts
        uses: actions/download-artifact@v3
        with:
          name: TraderAdmin-*
          path: artifacts/
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref }}
          name: Release ${{ github.ref }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Upload Release Assets
        uses: softprops/action-gh-release@v1
        with:
          files: artifacts/**
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 3. Testing & Validation

* **Lint & Type Check**: ensure no Svelte/TS errors on PRs
* **Build Verification**: on matrix runs, confirm binaries (e.g., `TraderAdmin.exe`, `.app`, Linux binary) exist in `build/bin`

## 4. Cucumber Scenarios

```gherkin
Feature: GUI CI/CD Pipeline
  Scenario: Lint and build on PR
    Given a PR against main
    When CI runs lint-and-build
    Then no lint or type errors occur
    And build/bin contains platform-specific binaries

  Scenario: Release on tag
    Given a new tag v1.0.0
    When CI runs release job
    Then a GitHub Release is created
    And artifacts for each OS are attached
```

## 5. Pseudocode Outline

```text
# On PR:
cd frontend && npm ci && npm run lint && npm run check
cd backend && go build
wails build
upload build/bin

# On tag:
download artifacts
create GitHub release
upload artifacts
```
