# 🛡️ Security Policy: Semantic-Sift

Semantic-Sift is a "Sovereign Sidecar" designed with a **Privacy-First, Security-Always** architecture. We take the security of your context and your machine seriously.

## 1. 🔍 Automated Audits
Our codebase and dependencies are automatically audited using the following "Cybersecurity Tier" tools:

- **Logic & Integrity**: [Pytest](https://pytest.org) — 100% pass rate on heuristic logic and privacy kill-switch verification.
- **Static Analysis (SAST)**: [Bandit](https://github.com/PyCQA/bandit) — Every line of Python is scanned for common security vulnerabilities and insecure patterns.
- **Dependency Audit (SCA)**: [Pip-Audit](https://github.com/pypa/pip-audit) — Our supply chain is scanned against the PyPA advisory database for known CVEs.

## 2. 🛡️ Reporting a Vulnerability
If you discover a potential security issue or secret-exposure risk, please do not open a public issue. Instead, please report it via the following channel:

- **Security Lead**: Luis Kobayashi
- **Channel**: [https://www.luiskobayashi.com/contact](https://www.luiskobayashi.com/contact)
- **Response Time**: We aim to acknowledge reports within 48 hours and provide a patch within 7 days for critical issues.

## 3. 🔒 Core Security Mandates
- **Local Sovereignty**: No raw data, code, or prompts ever leave your machine.
- **Zero Tracking**: We support the `SIFT_TELEMETRY_DISABLED=true` flag for absolute privacy.
- **Metadata-Only Telemetry**: Anonymous pulses contain only character/token counts and anonymous machine IDs.

---
*Building secure systems for the Studio of Two.*
