# InsightShop - AWS App Runner setup in us-east-1
# Prerequisites: AWS CLI installed and configured (aws configure)
# Run this once to create ECR repository and IAM roles. After first GitHub Actions deploy (image pushed), the workflow will create the App Runner service.

$ErrorActionPreference = "Stop"
$REGION = "us-east-1"
$ECR_REPO_NAME = "insightshop"
$APP_RUNNER_SERVICE_NAME = "insightshop"
$ACCESS_ROLE_NAME = "InsightShopAppRunnerECRAccess"
$INSTANCE_ROLE_NAME = "InsightShopAppRunnerInstanceRole"

Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""

# Get AWS account ID
Write-Host "Getting AWS account ID..."
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
if (-not $ACCOUNT_ID) { throw "Failed to get AWS account ID. Is AWS CLI configured?" }
Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green
$ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"
Write-Host "ECR image URI (use tag :latest): $ECR_URI" -ForegroundColor Green
Write-Host ""

# 1. Create ECR repository if it doesn't exist
Write-Host "Creating ECR repository '$ECR_REPO_NAME' if not exists..."
$repoExists = aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $REGION 2>$null
if (-not $repoExists) {
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $REGION
    Write-Host "ECR repository created." -ForegroundColor Green
} else {
    Write-Host "ECR repository already exists." -ForegroundColor Yellow
}
Write-Host ""

# 2. Create IAM role for App Runner to pull from ECR (Access Role)
Write-Host "Creating IAM access role for App Runner (ECR pull)..."
$trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
$trustPolicyFile = [System.IO.Path]::GetTempFileName()
$trustPolicy | Out-File -FilePath $trustPolicyFile -Encoding utf8
try {
    $roleExists = aws iam get-role --role-name $ACCESS_ROLE_NAME 2>$null
    if (-not $roleExists) {
        aws iam create-role --role-name $ACCESS_ROLE_NAME --assume-role-policy-document "file://$trustPolicyFile"
        aws iam attach-role-policy --role-name $ACCESS_ROLE_NAME --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
        Write-Host "Access role '$ACCESS_ROLE_NAME' created and policy attached." -ForegroundColor Green
    } else {
        Write-Host "Access role '$ACCESS_ROLE_NAME' already exists." -ForegroundColor Yellow
    }
} finally {
    Remove-Item -Path $trustPolicyFile -Force -ErrorAction SilentlyContinue
}
$ACCESS_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${ACCESS_ROLE_NAME}"
Write-Host "Access Role ARN: $ACCESS_ROLE_ARN" -ForegroundColor Green
Write-Host ""

# 3. Optional: Create IAM role for App Runner instance (e.g. Secrets Manager)
Write-Host "Creating IAM instance role (for Secrets Manager, etc.)..."
$instanceTrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
$instanceTrustFile = [System.IO.Path]::GetTempFileName()
$instanceTrustPolicy | Out-File -FilePath $instanceTrustFile -Encoding utf8
$instancePolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
"@
$instancePolicyFile = [System.IO.Path]::GetTempFileName()
$instancePolicy | Out-File -FilePath $instancePolicyFile -Encoding utf8
try {
    $instanceRoleExists = aws iam get-role --role-name $INSTANCE_ROLE_NAME 2>$null
    if (-not $instanceRoleExists) {
        aws iam create-role --role-name $INSTANCE_ROLE_NAME --assume-role-policy-document "file://$instanceTrustFile"
        aws iam put-role-policy --role-name $INSTANCE_ROLE_NAME --policy-name "SecretsManagerRead" --policy-document "file://$instancePolicyFile"
        Write-Host "Instance role '$INSTANCE_ROLE_NAME' created." -ForegroundColor Green
    } else {
        Write-Host "Instance role '$INSTANCE_ROLE_NAME' already exists." -ForegroundColor Yellow
    }
} finally {
    Remove-Item -Path $instanceTrustFile, $instancePolicyFile -Force -ErrorAction SilentlyContinue
}
$INSTANCE_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${INSTANCE_ROLE_NAME}"
Write-Host "Instance Role ARN: $INSTANCE_ROLE_ARN" -ForegroundColor Green
Write-Host ""

Write-Host "=== Next steps ===" -ForegroundColor Cyan
Write-Host "1. Add these GitHub repository secrets (Settings -> Secrets and variables -> Actions):"
Write-Host "   - AWS_ACCESS_KEY_ID"
Write-Host "   - AWS_SECRET_ACCESS_KEY"
Write-Host "   - APP_RUNNER_ACCESS_ROLE_ARN = $ACCESS_ROLE_ARN"
Write-Host "   - (Optional) APP_RUNNER_INSTANCE_ROLE_ARN = $INSTANCE_ROLE_ARN"
Write-Host ""
Write-Host "2. Push to the main branch. The GitHub Actions workflow will:"
Write-Host "   - Build the Docker image and push to ECR"
Write-Host "   - Create the App Runner service on first run (if not exists)"
Write-Host "   - Trigger a new deployment on every push to main"
Write-Host ""
Write-Host "3. If you use AWS Secrets Manager, set AWS_SECRETS_INSIGHTSHOP in App Runner"
Write-Host "   (e.g. via AWS Console -> App Runner -> Service -> Configuration -> Environment variables)"
Write-Host "   and use the instance role ARN above so the app can read the secret."
Write-Host ""
