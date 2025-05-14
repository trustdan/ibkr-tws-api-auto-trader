#!/bin/bash
# Script to help with versioning and releases

set -e

# Check if version is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

VERSION=$1
VERSION_TAG="v$VERSION"

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
    echo "Invalid version format. Expected: X.Y.Z or X.Y.Z-suffix"
    exit 1
fi

# Make sure we're in the repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean. Commit or stash changes first."
    exit 1
fi

echo "Preparing release $VERSION_TAG..."

# Update version in package.json
sed -i.bak "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json && rm frontend/package.json.bak
echo "✅ Updated version in frontend/package.json to $VERSION"

# Update any other version references in the app

# Commit version changes
git add frontend/package.json
git commit -m "chore: bump version to $VERSION"

# Create and push the tag
git tag -a "$VERSION_TAG" -m "Release $VERSION_TAG"
echo "✅ Created tag $VERSION_TAG"

echo ""
echo "Version updated to $VERSION"
echo ""
echo "To push the release to GitHub, run:"
echo "  git push origin main && git push origin $VERSION_TAG"
echo ""
echo "This will trigger the CI/CD pipeline to build and publish the release." 