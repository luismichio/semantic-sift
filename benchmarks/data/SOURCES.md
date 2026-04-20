# 📜 Benchmark Data Sources

The following samples are used as the "Ground Truth" for Semantic-Sift performance metrics.

| Sample | Source Origin | Description |
| :--- | :--- | :--- |
| `github_actions.txt` | [GitHub Runner Docs](https://github.com/actions/runner) | Raw diagnostic logs with `##[debug]` and `##[group]` markers. |
| `vercel_logs.txt` | [Vercel CLI Docs](https://vercel.com/docs/cli/logs) | Authentic build-time stdout/stderr from Next.js deployments. |
| `git_history.txt` | [Git Source Project](https://github.com/git/git) | Verbose commit history generated via `git log --date=iso --pretty=fuller`. |
| `git_diff.txt` | [Linux Kernel Diffs](https://github.com/torvalds/linux) | Complex, multi-hunk diffs with extensive metadata. |
| `npm_install.txt` | [NPM CLI Output](https://docs.npmjs.com) | Standard verbose installation logs with progress indicators. |

---
## 🧪 Verification
To verify these results, you can download raw logs from any public GitHub repository and drop them into this directory as `.txt` files.
