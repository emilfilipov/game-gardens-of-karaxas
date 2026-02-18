#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
POLICY_NAME="${POLICY_NAME:-karaxas-backend-policy}"
BACKEND_SERVICE="${BACKEND_SERVICE:-}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: PROJECT_ID=<gcp-project> [POLICY_NAME=karaxas-backend-policy] [BACKEND_SERVICE=<https-lb-backend-service>] $0" >&2
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null

if ! gcloud compute security-policies describe "$POLICY_NAME" >/dev/null 2>&1; then
  gcloud compute security-policies create "$POLICY_NAME" \
    --description "Baseline Cloud Armor policy for Gardens of Karaxas backend"
fi

# Default deny all high-volume non-browser abuse patterns.
if ! gcloud compute security-policies rules describe 1000 --security-policy "$POLICY_NAME" >/dev/null 2>&1; then
  gcloud compute security-policies rules create 1000 \
    --security-policy "$POLICY_NAME" \
    --expression "evaluatePreconfiguredExpr('xss-stable')" \
    --action "deny-403" \
    --description "Block common XSS probes"
fi

if ! gcloud compute security-policies rules describe 1010 --security-policy "$POLICY_NAME" >/dev/null 2>&1; then
  gcloud compute security-policies rules create 1010 \
    --security-policy "$POLICY_NAME" \
    --expression "evaluatePreconfiguredExpr('sqli-stable')" \
    --action "deny-403" \
    --description "Block common SQLi probes"
fi

if ! gcloud compute security-policies rules describe 2000 --security-policy "$POLICY_NAME" >/dev/null 2>&1; then
  gcloud compute security-policies rules create 2000 \
    --security-policy "$POLICY_NAME" \
    --expression "origin.region_code == 'CN'" \
    --action "deny-403" \
    --description "Example geo rule (adjust/remove for your market)"
fi

if [[ -n "$BACKEND_SERVICE" ]]; then
  gcloud compute backend-services update "$BACKEND_SERVICE" \
    --security-policy "$POLICY_NAME" \
    --global
  echo "Attached policy ${POLICY_NAME} to backend service ${BACKEND_SERVICE}"
else
  echo "Cloud Armor policy ${POLICY_NAME} configured. Attach it to a load balancer backend with:"
  echo "gcloud compute backend-services update <backend-service> --security-policy ${POLICY_NAME} --global"
fi
