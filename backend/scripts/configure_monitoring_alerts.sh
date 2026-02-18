#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
SERVICE_NAME="${SERVICE_NAME:-karaxas-backend}"
NOTIFICATION_CHANNEL="${NOTIFICATION_CHANNEL:-}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: PROJECT_ID=<gcp-project> [SERVICE_NAME=karaxas-backend] [NOTIFICATION_CHANNEL=projects/.../notificationChannels/...] $0" >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

channels_json="[]"
if [[ -n "$NOTIFICATION_CHANNEL" ]]; then
  channels_json="[\"$NOTIFICATION_CHANNEL\"]"
fi

cat >"$tmpdir/cloudrun-5xx.json" <<EOF
{
  "displayName": "Karaxas backend 5xx ratio high",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Cloud Run request 5xx ratio > 5%",
      "conditionThreshold": {
        "filter": "resource.type=\\"cloud_run_revision\\" AND resource.label.\\"service_name\\"=\\"$SERVICE_NAME\\" AND metric.type=\\"run.googleapis.com/request_count\\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "enabled": true,
  "notificationChannels": $channels_json,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

cat >"$tmpdir/cloudrun-latency.json" <<EOF
{
  "displayName": "Karaxas backend p95 latency high",
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Cloud Run latency p95 > 1.5s",
      "conditionThreshold": {
        "filter": "resource.type=\\"cloud_run_revision\\" AND resource.label.\\"service_name\\"=\\"$SERVICE_NAME\\" AND metric.type=\\"run.googleapis.com/request_latencies\\"",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_PERCENTILE_95"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 1.5,
        "duration": "300s",
        "trigger": {
          "count": 1
        }
      }
    }
  ],
  "enabled": true,
  "notificationChannels": $channels_json,
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF

echo "Creating monitoring alert policies in project ${PROJECT_ID}"
gcloud monitoring policies create --project "$PROJECT_ID" --policy-from-file "$tmpdir/cloudrun-5xx.json"
gcloud monitoring policies create --project "$PROJECT_ID" --policy-from-file "$tmpdir/cloudrun-latency.json"
echo "Alert policies created."
