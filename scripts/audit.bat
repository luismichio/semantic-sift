@echo off
echo ==========================================
echo "🔍 SEMANTIC-SIFT: SECURITY & LOGIC AUDIT"
echo ==========================================
echo.

set PYTHONPATH=.

echo "[1/4] Running Unit Tests (Logic & Privacy)..."
pytest tests/
if %errorlevel% neq 0 (
    echo "❌ Unit tests failed!"
    exit /b %errorlevel%
)
echo "✅ Tests Passed."
echo.

echo "[2/4] Running Static Security Scan (Bandit)..."
bandit -r server.py sift_hook.py telemetry_core.py -ll
if %errorlevel% neq 0 (
    echo "❌ Security vulnerabilities found!"
    exit /b %errorlevel%
)
echo "✅ Code Secure."
echo.

echo "[3/4] Auditing Dependencies (Pip-Audit)..."
pip-audit
if %errorlevel% neq 0 (
    echo "❌ Vulnerable dependencies detected!"
    exit /b %errorlevel%
)
echo "✅ Dependencies Clean."
echo.

echo "[4/5] Running Type Checks (mypy)..."
mypy server.py sift_kernel.py sift_hook.py telemetry_core.py semantic_sift
if %errorlevel% neq 0 (
    echo "❌ Type checking failed!"
    exit /b %errorlevel%
)
echo "✅ Type checks passed."
echo.

echo "[5/5] Running Linting (ruff)..."
ruff check .
if %errorlevel% neq 0 (
    echo "❌ Linting violations found!"
    exit /b %errorlevel%
)
echo "✅ Code Idiomatic."
echo.

echo ==========================================
echo "🏆 AUDIT COMPLETE: ALL SYSTEMS GREEN"
echo ==========================================
