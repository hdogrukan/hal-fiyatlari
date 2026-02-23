#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${SCRIPT_DIR}/cron_backfill.log"
LOCK_FILE="${SCRIPT_DIR}/.daily_backfill.lock"
MAIN_DB="${SCRIPT_DIR}/hal_fiyatlari.db"

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [[ -x "${SCRIPT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "python3 bulunamadi." >&2
  exit 1
fi

mkdir -p "${SCRIPT_DIR}"
touch "${LOG_FILE}"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] backfill start"
  if command -v flock >/dev/null 2>&1; then
    flock -n "${LOCK_FILE}" "${PYTHON_BIN}" "${SCRIPT_DIR}/backfill_hal_api.py" --db "${MAIN_DB}"
  else
    "${PYTHON_BIN}" "${SCRIPT_DIR}/backfill_hal_api.py" --db "${MAIN_DB}"
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] backfill end"
} >> "${LOG_FILE}" 2>&1
