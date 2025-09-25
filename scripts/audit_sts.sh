#!/usr/bin/env bash
set -euo pipefail
aws sts get-caller-identity \
  --output json | tee -a evidence/audit_sts.jsonl
