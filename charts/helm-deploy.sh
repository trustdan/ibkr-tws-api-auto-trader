#!/bin/bash
# Helper script for deploying the Helm chart

set -e

# Parse command line arguments
ENVIRONMENT=${1:-dev}
ACTION=${2:-install}
RELEASE_NAME=traderadmin-${ENVIRONMENT}
NAMESPACE=ibkr-trader-${ENVIRONMENT}
VALUES_FILE=${3:-values-${ENVIRONMENT}.yaml}

# Create values file for the environment if it doesn't exist
if [ ! -f "${VALUES_FILE}" ] && [ "${ENVIRONMENT}" != "default" ]; then
  echo "Creating ${VALUES_FILE} file..."
  cat > "${VALUES_FILE}" <<EOL
# ${ENVIRONMENT} environment values
namespace: ${NAMESPACE}

# Use environment-specific image tags
image:
  pythonOrch:
    tag: ${ENVIRONMENT}
  goScanner:
    tag: ${ENVIRONMENT}

# Configure resources based on environment
resources:
  pythonOrch:
    requests:
      cpu: $([ "${ENVIRONMENT}" == "prod" ] && echo "200m" || echo "100m")
      memory: $([ "${ENVIRONMENT}" == "prod" ] && echo "256Mi" || echo "128Mi")
    limits:
      cpu: $([ "${ENVIRONMENT}" == "prod" ] && echo "1000m" || echo "500m")
      memory: $([ "${ENVIRONMENT}" == "prod" ] && echo "1Gi" || echo "512Mi")
  goScanner:
    requests:
      cpu: $([ "${ENVIRONMENT}" == "prod" ] && echo "200m" || echo "100m")
      memory: $([ "${ENVIRONMENT}" == "prod" ] && echo "256Mi" || echo "128Mi")
    limits:
      cpu: $([ "${ENVIRONMENT}" == "prod" ] && echo "1000m" || echo "500m")
      memory: $([ "${ENVIRONMENT}" == "prod" ] && echo "1Gi" || echo "512Mi")
EOL
fi

# Function to perform Helm actions
perform_helm_action() {
  case "${ACTION}" in
    install)
      echo "Installing ${RELEASE_NAME} in namespace ${NAMESPACE}..."
      helm install ${RELEASE_NAME} ./traderadmin \
        --create-namespace \
        --namespace ${NAMESPACE} \
        $([ -f "${VALUES_FILE}" ] && echo "-f ${VALUES_FILE}")
      ;;
    upgrade)
      echo "Upgrading ${RELEASE_NAME} in namespace ${NAMESPACE}..."
      helm upgrade ${RELEASE_NAME} ./traderadmin \
        --namespace ${NAMESPACE} \
        $([ -f "${VALUES_FILE}" ] && echo "-f ${VALUES_FILE}")
      ;;
    uninstall)
      echo "Uninstalling ${RELEASE_NAME} from namespace ${NAMESPACE}..."
      helm uninstall ${RELEASE_NAME} --namespace ${NAMESPACE}
      ;;
    template)
      echo "Generating template for ${RELEASE_NAME}..."
      helm template ${RELEASE_NAME} ./traderadmin \
        --namespace ${NAMESPACE} \
        $([ -f "${VALUES_FILE}" ] && echo "-f ${VALUES_FILE}")
      ;;
    *)
      echo "Unknown action: ${ACTION}"
      echo "Usage: $0 [environment] [install|upgrade|uninstall|template] [values-file]"
      exit 1
      ;;
  esac
}

# Perform the helm action
perform_helm_action

# Output status if installing or upgrading
if [ "${ACTION}" == "install" ] || [ "${ACTION}" == "upgrade" ]; then
  echo "Waiting for deployments to become ready..."
  kubectl -n ${NAMESPACE} rollout status deployment/python-orch
  kubectl -n ${NAMESPACE} rollout status deployment/go-scanner
  kubectl -n ${NAMESPACE} rollout status deployment/redis

  echo ""
  echo "To port-forward the Python Orchestrator service:"
  echo "kubectl -n ${NAMESPACE} port-forward svc/python-orch 8000:8000"
  echo ""
  echo "To port-forward the Go Scanner metrics:"
  echo "kubectl -n ${NAMESPACE} port-forward svc/go-scanner 2112:2112"
fi 