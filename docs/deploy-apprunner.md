# Deploy InsightShop to AWS App Runner (us-east-1)

This guide sets up AWS App Runner in **us-east-1** and deploys the **frontend and backend** (Docker) on every push to the **main** branch via GitHub Actions.

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
- Creates the GitHub OIDC identity provider in IAM (if not present) and IAM role **InsightShopGitHubActionsRole** for GitHub Actions to assume (no long-lived access keys)

At the end it prints the GitHub secrets you need to add.

## 2. GitHub repository secrets

The workflow uses **OpenID Connect (OIDC)** to authenticate with AWS (no long-lived access keys). The setup script creates an IAM role that GitHub Actions can assume.

In your GitHub repo: **Settings → Secrets and variables → Actions**, add:

| Secret | Required | Description |
|--------|----------|-------------|
| `AWS_ROLE_ARN` | Yes | ARN of `InsightShopGitHubActionsRole` (for GitHub Actions to assume; printed by the script) |
| `APP_RUNNER_ACCESS_ROLE_ARN` | Yes | **Must be an IAM role with App Runner permissions.** Used by App Runner to pull the image from ECR. The script creates `InsightShopAppRunnerECRAccess` for this. |
| `APP_RUNNER_INSTANCE_ROLE_ARN` | No | **Must be an IAM role for your App Runner instance** (optional). Used by the running app (e.g. to read Secrets Manager). The script creates `InsightShopAppRunnerInstanceRole` for this. |
| `JWT_SECRET` | No | **Recommended for production.** At least 32 characters; used by the app when `FLASK_ENV=production`. If unset, the workflow uses a default so the service can start—set a strong value in App Runner or as this secret. |

You do **not** need `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`; the workflow uses OIDC with `role-to-assume`.

## 3. Deploy on push to main

- **First push to main**: The workflow builds the Docker image (frontend + backend), pushes it to ECR, **creates** the App Runner service via AWS CLI (if it does not exist), and waits for the first deployment.
- **Later pushes to main**: The workflow builds, pushes the new image, triggers a new App Runner deployment with `aws apprunner start-deployment`, and waits for it to finish.

Workflow file: [.github/workflows/deploy-apprunner.yml](../.github/workflows/deploy-apprunner.yml). The service is created using `aws apprunner create-service` when it does not exist.

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

## 6. Troubleshooting: if service creation fails

If the App Runner service ends up in **CREATE_FAILED**, use the AWS Console to see why:

**Where to look**

1. **Open App Runner**  
   AWS Console → search for **App Runner** in the top search bar → open App Runner.

2. **Open the service**  
   Click the **insightshop** service (it appears after the workflow runs create-service).

3. **Check why creation failed**
   - **Activity / Events** – List of operations (e.g. “Create service”, “Deploy”). Click the failed one to see status and the error message (e.g. image pull failure, health check failure).
   - **Details / Configuration** – Confirm source image, port (5000), health check path (`/api/health`), and IAM roles.
   - **Logs** (if available) – Application or deployment logs for startup or health check errors.

**Common causes of CREATE_FAILED**

- **Image pull** – ECR permissions or wrong image; ensure `APP_RUNNER_ACCESS_ROLE_ARN` is set and the role can pull from the ECR repo.
- **Health check** – App must respond to **GET /api/health** on port **5000** within the configured timeout.
- **Startup** – App crashes on start; check application logs in the console.

## 7. Create App Runner service via AWS CLI (optional)

If you want to create the service manually (e.g. after building and pushing the image yourself):

1. Ensure the image exists in ECR: `ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/insightshop:latest`
2. Create the service (replace placeholders with your access role ARN and optional instance role ARN):

```bash
aws apprunner create-service --region us-east-1 --cli-input-json file://create-service-input.json
```

Use the same JSON structure as the workflow: `ServiceName`, `SourceConfiguration` (ImageRepository with ECR, `AuthenticationConfiguration.AccessRoleArn`), `InstanceConfiguration`, `HealthCheckConfiguration` (Protocol HTTP, Path `/api/health`). See the workflow’s “Get or create App Runner service” step for the exact structure.
