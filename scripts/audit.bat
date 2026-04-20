@echo off
echo ==========================================
echo "🔍 SEMANTIC-SIFT: SECURITY & LOGIC AUDIT"
echo ==========================================
echo.

set PYTHONPATH=.

echo "[1/3] Running Unit Tests (Logic & Privacy)..."
pytest tests/
if %errorlevel% neq 0 (
    echo "❌ Unit tests failed!"
    exit /b %errorlevel%
)
echo "✅ Tests Passed."
echo.

echo "[2/3] Running Static Security Scan (Bandit)..."
bandit -r server.py sift_hook.py telemetry_core.py -ll
if %errorlevel% neq 0 (
    echo "❌ Security vulnerabilities found!"
    exit /b %errorlevel%
)
echo "✅ Code Secure."
echo.

echo "[3/3] Auditing Dependencies (Pip-Audit)..."
pip-audit
if %errorlevel% neq 0 (
    echo "❌ Vulnerable dependencies detected!"
    exit /b %errorlevel%
)
echo "✅ Dependencies Clean."
echo.

echo ==========================================
echo "🏆 AUDIT COMPLETE: ALL SYSTEMS GREEN"
echo ==========================================
