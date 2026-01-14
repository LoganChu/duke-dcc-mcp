#!/usr/bin/env bash
set -euo pipefail
USERNAME="$1"
kubectl delete namespace user-$USERNAME