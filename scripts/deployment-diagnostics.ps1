# Deployment diagnostics for InsightShop (GitHub Actions -> App Runner)
# Run after: gh auth login
# Usage: .\scripts\deployment-diagnostics.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "=== 1. Recent GitHub Actions workflow runs ===" -ForegroundColor Cyan
gh run list --workflow "deploy-apprunner.yml" --limit 10

Write-Host "`n=== 2. Latest run (full details) ===" -ForegroundColor Cyan
$latestRun = gh run list --workflow "deploy-apprunner.yml" --limit 1 --json databaseId,conclusion,status,name,displayTitle,createdAt,updatedAt --jq ".[0]"
if ($latestRun) {
    $latestRun | ConvertFrom-Json | Format-List
    $runId = (gh run list --workflow "deploy-apprunner.yml" --limit 1 --json databaseId --jq ".[0].databaseId")
    if ($runId) {
        Write-Host "`n=== 3. Failed job steps (if any) - Run ID: $runId ===" -ForegroundColor Cyan
        gh run view $runId --log-failed 2>&1
    }
} else {
    Write-Host "No runs found for deploy-apprunner.yml"
}

Write-Host "`n=== 4. App Runner service status (AWS) ===" -ForegroundColor Cyan
aws apprunner describe-service --region us-east-1 --service-arn "arn:aws:apprunner:us-east-1:255315172922:service/insightshop/a44de79d788e46df870d021342d2d087" --query "Service.{Status:Status,ServiceUrl:ServiceUrl,UpdatedAt:UpdatedAt}" --output table 2>&1

Write-Host "`n=== 5. Last 3 App Runner operations ===" -ForegroundColor Cyan
aws apprunner list-operations --region us-east-1 --service-arn "arn:aws:apprunner:us-east-1:255315172922:service/insightshop/a44de79d788e46df870d021342d2d087" --max-results 3 --query "OperationSummaryList[*].{Type:Type,Status:Status,StartedAt:StartedAt,EndedAt:EndedAt}" --output table 2>&1

Write-Host "`nDone. If the workflow failed, check the failed log above for the exact step and error." -ForegroundColor Green
