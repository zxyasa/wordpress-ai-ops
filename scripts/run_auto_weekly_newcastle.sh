#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs weekly-output-auto-live-gsc

# Load local env vars for non-interactive launchd runs.
# Parse KEY=VALUE literally (supports spaces in VALUE) without eval/source.
if [[ -f ".env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *"="* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    [[ "$value" =~ ^\".*\"$ ]] && value="${value:1:${#value}-2}"
    [[ "$value" =~ ^\'.*\'$ ]] && value="${value:1:${#value}-2}"
    export "${key}=${value}"
  done < ".env"
fi

TIMESTAMP_UTC="$(date -u +"%Y%m%dT%H%M%SZ")"
LOG_FILE="logs/auto-weekly-${TIMESTAMP_UTC}.log"
OUT_DIR="weekly-output-auto-live-gsc"

# Avoid stale task/report carry-over across runs.
rm -rf "${OUT_DIR}/tasks"
rm -f "${OUT_DIR}/weekly_report.json" "${OUT_DIR}/weekly_report.md"

{
  echo "[${TIMESTAMP_UTC}] start auto-weekly execute"

  WP_BASE="${WP_BASE_URL:-https://newcastlehub.info}"
  AUTH_URL_BASE="${WP_BASE%/}/wp-json/wp/v2/users/me?context=edit"
  AUTH_BODY="$(mktemp)"
  AUTH_SLOT="primary"
  AUTH_STATUS="000"
  BACKUP_STATUS=""
  ACTIVE_WP_USERNAME="${WP_USERNAME:-}"
  ACTIVE_WP_APP_PASSWORD="${WP_APP_PASSWORD:-}"

  precheck_auth() {
    local user="$1"
    local pass="$2"
    if [[ -z "${user}" || -z "${pass}" ]]; then
      echo "000"
      return
    fi
    local ts
    ts="$(date +%s)"
    local auth_url="${AUTH_URL_BASE}&_=${ts}"
    curl -sS \
      -H "Cache-Control: no-cache" \
      -H "Pragma: no-cache" \
      -u "${user}:${pass}" \
      -o "${AUTH_BODY}" \
      -w "%{http_code}" \
      "${auth_url}" || true
  }

  AUTH_STATUS="$(precheck_auth "${ACTIVE_WP_USERNAME}" "${ACTIVE_WP_APP_PASSWORD}")"
  if [[ "${AUTH_STATUS}" != "200" && -n "${WP_BACKUP_USERNAME:-}" && -n "${WP_BACKUP_APP_PASSWORD:-}" ]]; then
    echo "[${TIMESTAMP_UTC}] primary_auth_failed status=${AUTH_STATUS}; trying backup credentials"
    BACKUP_STATUS="$(precheck_auth "${WP_BACKUP_USERNAME}" "${WP_BACKUP_APP_PASSWORD}")"
    if [[ "${BACKUP_STATUS}" == "200" ]]; then
      AUTH_STATUS="${BACKUP_STATUS}"
      AUTH_SLOT="backup"
      ACTIVE_WP_USERNAME="${WP_BACKUP_USERNAME}"
      ACTIVE_WP_APP_PASSWORD="${WP_BACKUP_APP_PASSWORD}"
      echo "[${TIMESTAMP_UTC}] backup_auth_ok status=200"
    else
      echo "[${TIMESTAMP_UTC}] backup_auth_failed status=${BACKUP_STATUS}"
    fi
  fi

  if [[ "${AUTH_STATUS}" != "200" ]]; then
    AUTH_PREVIEW="$(tr '\n' ' ' < "${AUTH_BODY}" | head -c 260)"
    echo "[${TIMESTAMP_UTC}] auth_precheck_failed slot=${AUTH_SLOT} status=${AUTH_STATUS} url=${AUTH_URL_BASE}"
    echo "[${TIMESTAMP_UTC}] auth_precheck_body=${AUTH_PREVIEW}"

    if [[ -n "${TG_BOT_TOKEN:-}" && -n "${TG_CHAT_ID:-}" ]]; then
      ALERT_TEXT="WordPress AI Ops precheck failed on ${WP_BASE} (status ${AUTH_STATUS}, slot ${AUTH_SLOT}). Auto-weekly aborted before writes."
      curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TG_CHAT_ID}" \
        --data-urlencode "text=${ALERT_TEXT}" >/dev/null || true
    fi
    rm -f "${AUTH_BODY}"
    exit 1
  fi
  rm -f "${AUTH_BODY}"

  # Ensure the runner uses the credential set that passed precheck.
  export WP_USERNAME="${ACTIVE_WP_USERNAME}"
  export WP_APP_PASSWORD="${ACTIVE_WP_APP_PASSWORD}"
  echo "[${TIMESTAMP_UTC}] auth_precheck_ok status=200 slot=${AUTH_SLOT}"

  PYTHONPATH=src python3 -m wp_ai_ops.cli auto-weekly \
    --base-url https://newcastlehub.info \
    --gsc-property sc-domain:newcastlehub.info \
    --gsc-credentials /Users/michaelzhao/agents/agents/sweetsworld-seo-agent/gsc_credentials.json \
    --site-profile examples/site_profiles/newcastlehub.info.json \
    --out-dir "${OUT_DIR}" \
    --state-dir .wp-ai-ops-state-live \
    --mode execute \
    --top-n 8 \
    --include-meta \
    --confirm \
    --notify-telegram

  PYTHONPATH=src python3 -m wp_ai_ops.cli report-markdown \
    --weekly-report-json "${OUT_DIR}/weekly_report.json" \
    --out "${OUT_DIR}/weekly_report.md"

  PYTHONPATH=src python3 -m wp_ai_ops.cli handoff \
    --state-dir .wp-ai-ops-state-live \
    --base-url https://newcastlehub.info \
    --out STATUS.md

  echo "[${TIMESTAMP_UTC}] done"
} >> "${LOG_FILE}" 2>&1
