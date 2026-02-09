# Deploy InsightShop to AWS App Runner (us-east-1)

This guide sets up AWS App Runner in **us-east-1** and deploys the app on every push to the **main** branch via GitHub Actions.

## Prerequisites

- AWS CLI installed and configured (`aws configure`) with credentials that can create ECR, IAM, and App Runner resources
- GitHub repository with the InsightShop code
- Push access to the **main** branch

## 1. One-time AWS setup (run locally)

From the project root, run the PowerShell script (Windows) or use the equivalent AWS CLI commands in **us-east-1**:

```powershell
.\scripts\setup-apprunner.ps1
```

This script:

- Creates an ECR repository `insightshop` in **us-east-1**
- Creates IAM role **InsightShopAppRunnerECRAccess** (for App Runner to pull images from ECR)
- Creates IAM role **InsightShopAppRunnerInstanceRole** (optional; for Secrets Manager so the app can load `AWS_SECRETS_INSIGHTSHOP`)

At the end it prints the GitHub secrets you need to add.

## 2. GitHub repository secrets

In your GitHub repo: **Settings → Secrets and variables → Actions**, add:

| Secret | Required | Description |
|--------|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | AWS access key for deploy (ECR push, App Runner deploy) |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key |
| `APP_RUNNER_ACCESS_ROLE_ARN` | Yes | ARN of the role `InsightShopAppRunnerECRAccess` (printed by the script) |
| `APP_RUNNER_INSTANCE_ROLE_ARN` | No | ARN of `InsightShopAppRunnerInstanceRole` if you use Secrets Manager |

## 3. Deploy on push to main

- **First push to main**: The workflow builds the Docker image, pushes it to ECR, **creates** the App Runner service (if it does not exist), and waits for the first deployment.
- **Later pushes to main**: The workflow builds, pushes the new image, triggers a new App Runner deployment, and waits for it to finish.

Workflow file: [.github/workflows/deploy-apprunner.yml](../.github/workflows/deploy-apprunner.yml).

## 4. App Runner configuration

- **Port**: 5000 (Flask/Gunicorn)
- **Health check**: HTTP `GET /api/health` every 10s
- **Region**: us-east-1
- **Service name**: `insightshop`

To add environment variables (e.g. `AWS_SECRETS_INSIGHTSHOP`, `JWT_SECRET`), use the AWS Console: **App Runner → insightshop → Configuration → Edit → Environment variables**, or extend the workflow’s `ImageConfiguration.RuntimeEnvironmentVariables` and/or use **RuntimeEnvironmentSecrets** for values from Secrets Manager.

## 5. Get the live URL

After a successful run:

- In the workflow run, check the **Output service URL** step, or
- In AWS Console: **App Runner → insightshop → Default domain**

The app is served over HTTPS on that domain.
