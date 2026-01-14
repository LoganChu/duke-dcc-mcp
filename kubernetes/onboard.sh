#!/usr/bin/env bash
set -euo pipefail
USERNAME="$1"
IMAGE="${2:-myregistry/chatbot:latest}"
DIR=./templates


# Create namespace
kubectl apply -f $DIR/01-namespace.yaml -n default --context=... # or templated substitution
# Apply quota and limitrange
kubectl apply -f $DIR/02-resourcequota.yaml
kubectl apply -f $DIR/03-limitrange.yaml
# Create SA + RBAC
kubectl apply -f $DIR/04-serviceaccount-rbac.yaml
# PVC
kubectl apply -f $DIR/05-pvc.yaml
# Deployment/Service/Ingress
kubectl apply -f $DIR/06-deployment.yaml
kubectl apply -f $DIR/07-service.yaml
kubectl apply -f $DIR/08-ingress.yaml
# Optional: HPA, PDB, NetworkPolicy
kubectl apply -f $DIR/09-hpa.yaml || true
kubectl apply -f $DIR/10-pdb.yaml || true
kubectl apply -f $DIR/11-networkpolicy.yaml || true