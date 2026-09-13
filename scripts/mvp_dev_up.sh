#!/usr/bin/env bash
# scripts/mvp_dev_up.sh — FastAPI + Next.js 동시 부팅 (Git Bash)
#
# 사용법 (별도 터미널):
#   bash scripts/mvp_dev_up.sh
#
# 종료:
#   Ctrl+C — 양쪽 모두 종료
#
# 사전 조건:
#   1. uv run python scripts/mvp_local_db.py up — 별도 터미널에서 DB 살아있어야 함
#   2. .mvp_local_db_url 파일에 DATABASE_URL 있어야 함

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f ".mvp_local_db_url" ]; then
  echo "[mvp_dev_up] ERROR: .mvp_local_db_url 파일 없음. 먼저 DB 시작:"
  echo "  uv run python scripts/mvp_local_db.py up"
  exit 1
fi

export DATABASE_URL="$(cat .mvp_local_db_url)"
export OTEL_SDK_DISABLED="true"
export SUPABASE_JWT_SECRET="test-jwt-secret-for-mvp-local-32chars-minimum"
export JWT_SECRET="test-jwt-secret-for-mvp-local-32chars-minimum"

echo "[mvp_dev_up] DATABASE_URL=$DATABASE_URL"
echo "[mvp_dev_up] starting FastAPI on :8000 + Next.js on :3000"
echo "[mvp_dev_up] 종료: Ctrl+C"

# 두 프로세스 동시 실행. 한 쪽 종료 시 다른 쪽도 종료.
cleanup() {
  echo "[mvp_dev_up] cleaning up..."
  kill $FASTAPI_PID $WEB_PID 2>/dev/null || true
  wait 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

uv run uvicorn apps.api.main:app --reload --port 8000 &
FASTAPI_PID=$!

(cd apps/web && pnpm dev) &
WEB_PID=$!

wait
