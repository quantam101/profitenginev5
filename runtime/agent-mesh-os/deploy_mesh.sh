#!/usr/bin/env bash
# ==============================================================================
# AGENT_MESH_OS — PRODUCTION BOOTSTRAP
# ==============================================================================
# Usage: ./deploy_mesh.sh
# Prerequisites: Docker, .env file with REDIS_PASSWORD + WORKDIR
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if present, otherwise use defaults
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a && source "${SCRIPT_DIR}/.env" && set +a
fi

WORKDIR="${WORKDIR:-/home/opc/agent_mesh_os}"
DATA_DIR="${WORKDIR}/data"
LOG_DIR="${WORKDIR}/logs"
REDIS_DATA="${WORKDIR}/redis_data"
STATE_DB="${DATA_DIR}/state/agent_mesh_state.db"

echo "======================================================================"
echo "AGENT_MESH_OS — STAGING PRODUCTION WORKSPACE"
echo "WORKDIR: ${WORKDIR}"
echo "======================================================================"

# ── Validate prerequisites ────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo "[ERROR] Docker not found in PATH." >&2
    exit 1
fi

if [[ -z "${REDIS_PASSWORD:-}" ]]; then
    echo "[ERROR] REDIS_PASSWORD is not set. Copy .env.example to .env and fill it." >&2
    exit 1
fi

# ── Create directory structure ────────────────────────────────────────────
mkdir -p "${DATA_DIR}/ollama" "${DATA_DIR}/state" "${LOG_DIR}" "${REDIS_DATA}"

# ── Initialize SQLite WAL journal (app-side, not a container) ────────────
# SQLite is a file — no container needed. Initialize here at deploy time.
if ! command -v sqlite3 &>/dev/null; then
    echo "[WARN] sqlite3 not found — installing..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y sqlite3
    elif command -v yum &>/dev/null; then
        sudo yum install -y sqlite
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y sqlite
    else
        echo "[ERROR] Cannot install sqlite3 automatically. Install manually." >&2
        exit 1
    fi
fi

echo "[*] Initializing SQLite WAL state database..."
sqlite3 "${STATE_DB}" <<'SQL'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA wal_autocheckpoint=1000;
CREATE TABLE IF NOT EXISTS system_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent     TEXT NOT NULL,
    payload   TEXT,
    status    TEXT DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_system_logs_agent ON system_logs(agent);
CREATE INDEX IF NOT EXISTS idx_system_logs_status ON system_logs(status);
CREATE TABLE IF NOT EXISTS agent_state (
    agent_id  TEXT PRIMARY KEY,
    state     TEXT DEFAULT 'idle',
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata  TEXT
);
SQL
echo "[+] SQLite WAL database ready: ${STATE_DB}"

# ── Start services ────────────────────────────────────────────────────────
echo "[*] Starting microservices..."
cd "${SCRIPT_DIR}"
docker compose --env-file .env up -d

# ── Wait for Redis ────────────────────────────────────────────────────────
echo "[*] Waiting for Redis broker..."
ATTEMPTS=0
until docker exec am_os_redis_broker redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q PONG; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ $ATTEMPTS -gt 20 ]]; then
        echo "[ERROR] Redis failed to start after 40 seconds." >&2
        docker logs am_os_redis_broker --tail 20
        exit 1
    fi
    sleep 2
done
echo "[+] Redis broker online."

# ── Wait for Ollama ───────────────────────────────────────────────────────
echo "[*] Waiting for Ollama inference engine..."
ATTEMPTS=0
until docker exec am_os_ollama_edge ollama list &>/dev/null; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ $ATTEMPTS -gt 30 ]]; then
        echo "[ERROR] Ollama failed to start after 60 seconds." >&2
        docker logs am_os_ollama_edge --tail 20
        exit 1
    fi
    sleep 2
done
echo "[+] Ollama edge engine online."

# ── Pull models — RAM-safe for 24GB OCI server ───────────────────────────
# llama3.1:8b-instruct-q4_K_M = ~4.7GB RAM (fast, fits easily)
# llama3.1:8b-instruct-q8_0   = ~8.6GB RAM (higher quality, still fits)
# DO NOT pull 70B models — they require 40-70GB RAM and will OOM the server

echo "[*] Pulling llama3.1:8b-instruct-q4_K_M (4.7GB — fast inference)..."
docker exec am_os_ollama_edge ollama pull llama3.1:8b-instruct-q4_K_M

echo "[*] Pulling qwen2.5:7b-instruct-q4_K_M (4.1GB — strong multilingual)..."
docker exec am_os_ollama_edge ollama pull qwen2.5:7b-instruct-q4_K_M

echo ""
echo "======================================================================"
echo "[+] AGENT_MESH_OS FULLY OPERATIONAL"
echo "    Redis:  127.0.0.1:6379"
echo "    Ollama: 127.0.0.1:11434"
echo "    SQLite: ${STATE_DB}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  Set GATEWAY_URL=http://127.0.0.1:4000 if using the LiteLLM hypervisor"
echo "  Add redis://127.0.0.1:6379 as broker in n8n or any agent framework"
echo "  SQLite is ready at ${STATE_DB} — import into Growth Command OS"
