@echo off
:: Helper script for deploying the Helm chart

:: Parse command line arguments
set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

set ACTION=%2
if "%ACTION%"=="" set ACTION=install

set RELEASE_NAME=traderadmin-%ENVIRONMENT%
set NAMESPACE=ibkr-trader-%ENVIRONMENT%

set VALUES_FILE=%3
if "%VALUES_FILE%"=="" set VALUES_FILE=values-%ENVIRONMENT%.yaml

:: Create values file for the environment if it doesn't exist
if not exist "%VALUES_FILE%" (
  if not "%ENVIRONMENT%"=="default" (
    echo Creating %VALUES_FILE% file...
    
    echo # %ENVIRONMENT% environment values > %VALUES_FILE%
    echo namespace: %NAMESPACE% >> %VALUES_FILE%
    echo. >> %VALUES_FILE%
    echo # Use environment-specific image tags >> %VALUES_FILE%
    echo image: >> %VALUES_FILE%
    echo   pythonOrch: >> %VALUES_FILE%
    echo     tag: %ENVIRONMENT% >> %VALUES_FILE%
    echo   goScanner: >> %VALUES_FILE%
    echo     tag: %ENVIRONMENT% >> %VALUES_FILE%
    echo. >> %VALUES_FILE%
    echo # Configure resources based on environment >> %VALUES_FILE%
    echo resources: >> %VALUES_FILE%
    echo   pythonOrch: >> %VALUES_FILE%
    echo     requests: >> %VALUES_FILE%
    
    if "%ENVIRONMENT%"=="prod" (
      echo       cpu: 200m >> %VALUES_FILE%
      echo       memory: 256Mi >> %VALUES_FILE%
      echo     limits: >> %VALUES_FILE%
      echo       cpu: 1000m >> %VALUES_FILE%
      echo       memory: 1Gi >> %VALUES_FILE%
    ) else (
      echo       cpu: 100m >> %VALUES_FILE%
      echo       memory: 128Mi >> %VALUES_FILE%
      echo     limits: >> %VALUES_FILE%
      echo       cpu: 500m >> %VALUES_FILE%
      echo       memory: 512Mi >> %VALUES_FILE%
    )
    
    echo   goScanner: >> %VALUES_FILE%
    echo     requests: >> %VALUES_FILE%
    
    if "%ENVIRONMENT%"=="prod" (
      echo       cpu: 200m >> %VALUES_FILE%
      echo       memory: 256Mi >> %VALUES_FILE%
      echo     limits: >> %VALUES_FILE%
      echo       cpu: 1000m >> %VALUES_FILE%
      echo       memory: 1Gi >> %VALUES_FILE%
    ) else (
      echo       cpu: 100m >> %VALUES_FILE%
      echo       memory: 128Mi >> %VALUES_FILE%
      echo     limits: >> %VALUES_FILE%
      echo       cpu: 500m >> %VALUES_FILE%
      echo       memory: 512Mi >> %VALUES_FILE%
    )
  )
)

:: Perform Helm action
if "%ACTION%"=="install" (
  echo Installing %RELEASE_NAME% in namespace %NAMESPACE%...
  helm install %RELEASE_NAME% .\traderadmin --create-namespace --namespace %NAMESPACE% -f %VALUES_FILE%
  goto post_install
) else if "%ACTION%"=="upgrade" (
  echo Upgrading %RELEASE_NAME% in namespace %NAMESPACE%...
  helm upgrade %RELEASE_NAME% .\traderadmin --namespace %NAMESPACE% -f %VALUES_FILE%
  goto post_install
) else if "%ACTION%"=="uninstall" (
  echo Uninstalling %RELEASE_NAME% from namespace %NAMESPACE%...
  helm uninstall %RELEASE_NAME% --namespace %NAMESPACE%
  goto end
) else if "%ACTION%"=="template" (
  echo Generating template for %RELEASE_NAME%...
  helm template %RELEASE_NAME% .\traderadmin --namespace %NAMESPACE% -f %VALUES_FILE%
  goto end
) else (
  echo Unknown action: %ACTION%
  echo Usage: %0 [environment] [install^|upgrade^|uninstall^|template] [values-file]
  goto end
)

:post_install
:: Wait for deployments to become ready if installing or upgrading
echo Waiting for deployments to become ready...
kubectl -n %NAMESPACE% rollout status deployment/python-orch
kubectl -n %NAMESPACE% rollout status deployment/go-scanner
kubectl -n %NAMESPACE% rollout status deployment/redis

echo.
echo To port-forward the Python Orchestrator service:
echo kubectl -n %NAMESPACE% port-forward svc/python-orch 8000:8000
echo.
echo To port-forward the Go Scanner metrics:
echo kubectl -n %NAMESPACE% port-forward svc/go-scanner 2112:2112

:end 