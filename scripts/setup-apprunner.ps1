# InsightShop - AWS App Runner setup in us-east-1
# Prerequisites: AWS CLI installed and configured (aws configure)
# Run this once to create ECR repository and IAM roles. After first GitHub Actions deploy (image pushed), the workflow will create the App Runner service.

$ErrorActionPreference = "Stop"
# Run AWS CLI via cmd so stderr (e.g. ".py" messages on some Windows setups) doesn't stop the script
function Run-Aws { cmd /c "aws $args 2>nul" }
$REGION = "us-east-1"
$ECR_REPO_NAME = "insightshop"
$APP_RUNNER_SERVICE_NAME = "insightshop"
$ACCESS_ROLE_NAME = "InsightShopAppRunnerECRAccess"
$INSTANCE_ROLE_NAME = "InsightShopAppRunnerInstanceRole"
# GitHub repo for OIDC trust policy (owner/repo). Must match your repository so Actions can assume the role.
$GITHUB_REPO = "aminparva84/InsightShop"

Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""

# Get AWS account ID
Write-Host "Getting AWS account ID..."
$ACCOUNT_ID = Run-Aws sts get-caller-identity --query Account --output text
if (-not $ACCOUNT_ID) { throw "Failed to get AWS account ID. Is AWS CLI configured?" }
Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green
$ECR_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"
Write-Host "ECR image URI (use tag :latest): $ECR_URI" -ForegroundColor Green
Write-Host ""

# 1. Create ECR repository if it doesn't exist
Write-Host "Creating ECR repository '$ECR_REPO_NAME' if not exists..."
$repoExists = Run-Aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $REGION
if (-not $repoExists) {
    Run-Aws ecr create-repository --repository-name $ECR_REPO_NAME --region $REGION | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "ECR repository created." -ForegroundColor Green
    } else {
        Write-Host "ECR create returned an error (repository may already exist). Continuing." -ForegroundColor Yellow
    }
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
    $roleExists = Run-Aws iam get-role --role-name $ACCESS_ROLE_NAME
    if (-not $roleExists) {
        Run-Aws iam create-role --role-name $ACCESS_ROLE_NAME --assume-role-policy-document "file://$trustPolicyFile" | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "Access role '$ACCESS_ROLE_NAME' created." -ForegroundColor Green }
        else { Write-Host "Access role create returned an error (may already exist). Continuing." -ForegroundColor Yellow }
    } else {
        Write-Host "Access role '$ACCESS_ROLE_NAME' already exists." -ForegroundColor Yellow
    }
    Run-Aws iam attach-role-policy --role-name $ACCESS_ROLE_NAME --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess" | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "Attach policy returned an error (may already be attached). Continuing." -ForegroundColor Yellow }
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
    $instanceRoleExists = Run-Aws iam get-role --role-name $INSTANCE_ROLE_NAME
    if (-not $instanceRoleExists) {
        Run-Aws iam create-role --role-name $INSTANCE_ROLE_NAME --assume-role-policy-document "file://$instanceTrustFile" | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "Instance role create returned an error (may already exist). Continuing." -ForegroundColor Yellow }
        else { Write-Host "Instance role '$INSTANCE_ROLE_NAME' created." -ForegroundColor Green }
    } else {
        Write-Host "Instance role '$INSTANCE_ROLE_NAME' already exists." -ForegroundColor Yellow
    }
    Run-Aws iam put-role-policy --role-name $INSTANCE_ROLE_NAME --policy-name "SecretsManagerRead" --policy-document "file://$instancePolicyFile" | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "Put instance role policy returned an error. Continuing." -ForegroundColor Yellow }
} finally {
    Remove-Item -Path $instanceTrustFile, $instancePolicyFile -Force -ErrorAction SilentlyContinue
}
$INSTANCE_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${INSTANCE_ROLE_NAME}"
Write-Host "Instance Role ARN: $INSTANCE_ROLE_ARN" -ForegroundColor Green
Write-Host ""

# 4. GitHub OIDC provider and IAM role for GitHub Actions (no long-lived access keys)
$OIDC_PROVIDER_ARN = "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
$GITHUB_ACTIONS_ROLE_NAME = "InsightShopGitHubActionsRole"
# Thumbprint for token.actions.githubusercontent.com (GitHub's OIDC)
$OIDC_THUMBPRINT = "6938fd4d98bab03faadb97b34396831e3780aea1"

Write-Host "Creating GitHub OIDC identity provider (if not exists)..."
$oidcExists = Run-Aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')]" --output text
if (-not $oidcExists) {
    Run-Aws iam create-open-id-connect-provider --url "https://token.actions.githubusercontent.com" --client-id-list "sts.amazonaws.com" --thumbprint-list $OIDC_THUMBPRINT | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "OIDC provider created." -ForegroundColor Green }
    else { Write-Host "OIDC provider create returned an error (may already exist). Continuing." -ForegroundColor Yellow }
} else {
    Write-Host "OIDC provider already exists." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Creating IAM role for GitHub Actions (OIDC)..."
$githubTrustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "$OIDC_PROVIDER_ARN"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
"@
$githubTrustFile = [System.IO.Path]::GetTempFileName()
$githubTrustPolicy | Out-File -FilePath $githubTrustFile -Encoding utf8 -NoNewline

$githubPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "ECRPush",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": "arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/${ECR_REPO_NAME}"
    },
    {
      "Sid": "AppRunner",
      "Effect": "Allow",
      "Action": [
        "apprunner:CreateService",
        "apprunner:ListServices",
        "apprunner:DescribeService",
        "apprunner:StartDeployment",
        "apprunner:DescribeOperation",
        "apprunner:ListOperations"
      ],
      "Resource": "*"
    },
    {
      "Sid": "PassRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "$ACCESS_ROLE_ARN",
        "$INSTANCE_ROLE_ARN"
      ]
    }
  ]
}
"@
$githubPolicyFile = [System.IO.Path]::GetTempFileName()
$githubPolicy | Out-File -FilePath $githubPolicyFile -Encoding utf8 -NoNewline

try {
    $ghRoleExists = Run-Aws iam get-role --role-name $GITHUB_ACTIONS_ROLE_NAME 2>$null; $roleExists = $LASTEXITCODE -eq 0
    if (-not $roleExists) {
        Run-Aws iam create-role --role-name $GITHUB_ACTIONS_ROLE_NAME --assume-role-policy-document "file://$githubTrustFile" | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "GitHub Actions role create returned an error (may already exist). Continuing." -ForegroundColor Yellow }
        else { Write-Host "GitHub Actions role '$GITHUB_ACTIONS_ROLE_NAME' created." -ForegroundColor Green }
    } else {
        Write-Host "GitHub Actions role '$GITHUB_ACTIONS_ROLE_NAME' already exists. Updating trust policy for repo $GITHUB_REPO." -ForegroundColor Yellow
        Run-Aws iam update-assume-role-policy --role-name $GITHUB_ACTIONS_ROLE_NAME --policy-document "file://$githubTrustFile" | Out-Null
    }
    Run-Aws iam put-role-policy --role-name $GITHUB_ACTIONS_ROLE_NAME --policy-name "InsightShopDeploy" --policy-document "file://$githubPolicyFile" | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "GitHub Actions role policy set/updated." -ForegroundColor Green }
    else { Write-Host "Put role policy returned an error. Check IAM permissions." -ForegroundColor Yellow }
} finally {
    Remove-Item -Path $githubTrustFile, $githubPolicyFile -Force -ErrorAction SilentlyContinue
}
$GITHUB_ACTIONS_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${GITHUB_ACTIONS_ROLE_NAME}"
Write-Host "GitHub Actions Role ARN: $GITHUB_ACTIONS_ROLE_ARN" -ForegroundColor Green
Write-Host ""

Write-Host "=== Next steps ===" -ForegroundColor Cyan
Write-Host "1. Add these GitHub repository secrets (Settings -> Secrets and variables -> Actions):"
Write-Host "   - AWS_ROLE_ARN = $GITHUB_ACTIONS_ROLE_ARN"
Write-Host "   - APP_RUNNER_ACCESS_ROLE_ARN = $ACCESS_ROLE_ARN"
Write-Host "     (Must be an IAM role with App Runner permissions; used to pull image from ECR.)"
Write-Host "   - (Optional) APP_RUNNER_INSTANCE_ROLE_ARN = $INSTANCE_ROLE_ARN"
Write-Host "     (Must be an IAM role for your App Runner instance; e.g. for Secrets Manager.)"
Write-Host "   (No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed; the workflow uses OIDC.)"
Write-Host ""
Write-Host "2. Trust policy is set to repo: $GITHUB_REPO (edit GITHUB_REPO at top of this script if different)."
Write-Host ""
Write-Host "3. Push to the main branch. The GitHub Actions workflow will:"
Write-Host "   - Build the Docker image and push to ECR"
Write-Host "   - Create the App Runner service on first run (if not exists)"
Write-Host "   - Trigger a new deployment on every push to main"
Write-Host ""
Write-Host "4. If you use AWS Secrets Manager, set AWS_SECRETS_INSIGHTSHOP in App Runner"
Write-Host "   (e.g. via AWS Console -> App Runner -> Service -> Configuration -> Environment variables)"
Write-Host "   and use the instance role ARN above so the app can read the secret."
Write-Host ""
exit 0