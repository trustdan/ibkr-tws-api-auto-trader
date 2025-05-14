@echo off
REM Script to help with versioning and releases on Windows

setlocal enabledelayedexpansion

REM Check if version is provided
if "%~1"=="" (
    echo Usage: %0 ^<version^>
    echo Example: %0 1.0.0
    exit /b 1
)

set VERSION=%~1
set VERSION_TAG=v%VERSION%

REM Validate version format (basic validation)
echo %VERSION% | findstr /r "^[0-9]\+\.[0-9]\+\.[0-9]\+\(-[a-zA-Z0-9]\+\)\?$" >nul
if errorlevel 1 (
    echo Invalid version format. Expected: X.Y.Z or X.Y.Z-suffix
    exit /b 1
)

REM Make sure we're in the repository root
cd %~dp0..

REM Check if working directory is clean
git status --porcelain > status.tmp
set /p STATUS=<status.tmp
del status.tmp
if not "%STATUS%"=="" (
    echo Error: Working directory is not clean. Commit or stash changes first.
    exit /b 1
)

echo Preparing release %VERSION_TAG%...

REM Update version in package.json using powershell
powershell -Command "(Get-Content frontend/package.json) -replace '\"version\": \".*\"', '\"version\": \"%VERSION%\"' | Set-Content frontend/package.json"
echo ✅ Updated version in frontend/package.json to %VERSION%

REM Commit version changes
git add frontend/package.json
git commit -m "chore: bump version to %VERSION%"

REM Create and push the tag
git tag -a "%VERSION_TAG%" -m "Release %VERSION_TAG%"
echo ✅ Created tag %VERSION_TAG%

echo.
echo Version updated to %VERSION%
echo.
echo To push the release to GitHub, run:
echo   git push origin main ^&^& git push origin %VERSION_TAG%
echo.
echo This will trigger the CI/CD pipeline to build and publish the release. 