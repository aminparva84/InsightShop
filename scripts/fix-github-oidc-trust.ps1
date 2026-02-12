# Fix GitHub Actions OIDC trust policy for InsightShop
# Run this once if you get "Not authorized to perform sts:AssumeRoleWithWebIdentity"
# Updates the IAM role to allow your specific GitHub repo (no wildcard).

$ErrorActionPreference = "Stop"
function Run-Aws { cmd /c "aws $args 2>nul" }

$GITHUB_ACTIONS_ROLE_NAME = "InsightShopGitHubActionsRole"
$GITHUB_REPO = "aminparva84/InsightShop"

Write-Host "Getting AWS account ID..."
$ACCOUNT_ID = Run-Aws sts get-caller-identity --query Account --output text
if (-not $ACCOUNT_ID) { throw "Failed to get AWS account ID. Is AWS CLI configured?" }

$OIDC_PROVIDER_ARN = "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

$trustPolicy = @"
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

$trustFile = [System.IO.Path]::GetTempFileName()
$trustPolicy | Out-File -FilePath $trustFile -Encoding utf8 -NoNewline

try {
    Write-Host "Updating trust policy for role $GITHUB_ACTIONS_ROLE_NAME (repo: $GITHUB_REPO)..."
    Run-Aws iam update-assume-role-policy --role-name $GITHUB_ACTIONS_ROLE_NAME --policy-document "file://$trustFile"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Done. Re-run your GitHub Actions workflow." -ForegroundColor Green
    } else {
        Write-Host "Update failed. Check AWS CLI output above." -ForegroundColor Red
        exit 1
    }
} finally {
    Remove-Item -Path $trustFile -Force -ErrorAction SilentlyContinue
}
