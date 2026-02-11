# GitHub Secrets Reference (InsightShop App Runner)

Use these values when adding **Secrets and variables → Actions** in your GitHub repo.

**AWS Account ID:** `255315172922`

---

## Required secrets

| Secret name | Value (copy exactly) |
|-------------|----------------------|
| **APP_RUNNER_ACCESS_ROLE_ARN** | `arn:aws:iam::255315172922:role/InsightShopAppRunnerECRAccess` |

---

## Optional secret

| Secret name | Value (copy exactly) |
|-------------|----------------------|
| **APP_RUNNER_INSTANCE_ROLE_ARN** | `arn:aws:iam::255315172922:role/InsightShopAppRunnerInstanceRole` |

---

Add them in GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
Use the **Secret name** in the table and paste the **Value** (including the full `arn:aws:iam::...` string).
