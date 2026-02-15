# InsightShop - Create RDS PostgreSQL + App Runner VPC connector for us-east-1
# Prerequisites: AWS CLI installed and configured.
# Run from project root. Only -DbPassword is required; VPC and subnets are auto-discovered from default VPC if omitted.
# After this, add DATABASE_URL to App Runner and set the VPC connector on the service. The app auto-creates the DB on first run.

param(
    [Parameter(Mandatory = $false)]
    [string] $VpcId,          # Optional: default VPC is used if not set
    [Parameter(Mandatory = $false)]
    [string[]] $SubnetIds,    # Optional: first 2 subnets of the VPC are used if not set
    [Parameter(Mandatory = $true)]
    [string] $DbPassword,
    [string] $Region = "us-east-1",
    [string] $DbInstanceId = "insightshop-db",
    [string] $DbName = "insightshop",
    [string] $DbUsername = "postgres",
    [string] $VpcConnectorName = "insightshop-connector"
)

$ErrorActionPreference = "Continue"
function Run-Aws { & aws @args 2>&1 | Out-String }

$REGION = $Region

# Auto-discover VPC and subnets if not provided
if (-not $VpcId) {
    Write-Host "Auto-discovering default VPC..." -ForegroundColor Cyan
    $VpcId = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --region $REGION --query "Vpcs[0].VpcId" --output text
    if (-not $VpcId -or $VpcId -eq "None") { throw "No default VPC found. Set -VpcId and -SubnetIds explicitly." }
    Write-Host "Using default VPC: $VpcId" -ForegroundColor Green
}
if (-not $SubnetIds -or $SubnetIds.Count -lt 2) {
    Write-Host "Auto-discovering subnets in VPC $VpcId..." -ForegroundColor Cyan
    $subnetList = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" --region $REGION --query "Subnets[*].SubnetId" --output text
    $SubnetIds = $subnetList -split "\s+" | Where-Object { $_ } | Select-Object -First 2
    if (-not $SubnetIds -or $SubnetIds.Count -lt 2) { throw "VPC must have at least 2 subnets. Add subnets or set -SubnetIds." }
    Write-Host "Using subnets: $($SubnetIds -join ', ')" -ForegroundColor Green
    Write-Host "Note: App Runner VPC connector works best with private subnets. If deployment fails, use -SubnetIds with private subnet IDs." -ForegroundColor Yellow
}
if ($SubnetIds -is [string]) { $SubnetIds = $SubnetIds -split "," | ForEach-Object { $_.Trim() } }

Write-Host "Region: $REGION, VPC: $VpcId, Subnets: $($SubnetIds -join ', ')" -ForegroundColor Cyan
Write-Host ""

# 1. Get VPC CIDR for RDS security group (allow App Runner traffic from VPC)
Write-Host "Getting VPC CIDR..."
$vpc = aws ec2 describe-vpcs --vpc-ids $VpcId --region $REGION --query "Vpcs[0].CidrBlock" --output text
if (-not $vpc -or $vpc -eq "None") { throw "Could not get VPC $VpcId" }
Write-Host "VPC CIDR: $vpc" -ForegroundColor Green

# 2. DB subnet group
$subnetGroupName = "insightshop-db-subnets"
Write-Host "Creating DB subnet group '$subnetGroupName'..."
$null = aws rds describe-db-subnet-groups --db-subnet-group-name $subnetGroupName --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    $null = aws rds create-db-subnet-group `
        --db-subnet-group-name $subnetGroupName `
        --db-subnet-group-description "Subnets for InsightShop RDS" `
        --subnet-ids $SubnetIds `
        --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Host "DB subnet group created." -ForegroundColor Green }
    else { Write-Host "DB subnet group create failed (may already exist)." -ForegroundColor Yellow }
} else { Write-Host "DB subnet group already exists." -ForegroundColor Yellow }
Write-Host ""

# 3. Security group for RDS (5432 from VPC + 18.193.0.149)
$rdsSgName = "insightshop-rds-sg"
$rdsSgId = $null
$sgs = aws ec2 describe-security-groups --filters "Name=group-name,Values=$rdsSgName" "Name=vpc-id,Values=$VpcId" --region $REGION --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($sgs -and $sgs -ne "None") { $rdsSgId = $sgs; Write-Host "RDS security group exists: $rdsSgId" -ForegroundColor Yellow }
else {
    $out = aws ec2 create-security-group --group-name $rdsSgName --description "RDS PostgreSQL for InsightShop" --vpc-id $VpcId --region $REGION --output json
    $rdsSgId = ($out | ConvertFrom-Json).GroupId
    Write-Host "Created RDS security group: $rdsSgId" -ForegroundColor Green
    aws ec2 authorize-security-group-ingress --group-id $rdsSgId --protocol tcp --port 5432 --cidr $vpc --region $REGION 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "  Rule: 5432 from VPC $vpc" -ForegroundColor Green }
    aws ec2 authorize-security-group-ingress --group-id $rdsSgId --protocol tcp --port 5432 --cidr "18.193.0.149/32" --region $REGION 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "  Rule: 5432 from 18.193.0.149 (DBeaver)" -ForegroundColor Green }
}
Write-Host ""

# 4. Security group for VPC connector (optional; App Runner can use default)
$connectorSgName = "insightshop-apprunner-connector-sg"
$connectorSgId = $null
$csgs = aws ec2 describe-security-groups --filters "Name=group-name,Values=$connectorSgName" "Name=vpc-id,Values=$VpcId" --region $REGION --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($csgs -and $csgs -ne "None") { $connectorSgId = $csgs; Write-Host "VPC connector SG exists: $connectorSgId" -ForegroundColor Yellow }
else {
    $out = aws ec2 create-security-group --group-name $connectorSgName --description "App Runner VPC connector" --vpc-id $VpcId --region $REGION --output json
    $connectorSgId = ($out | ConvertFrom-Json).GroupId
    Write-Host "Created VPC connector security group: $connectorSgId" -ForegroundColor Green
}
Write-Host ""

# 5. Create RDS PostgreSQL
$rdsExists = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $REGION 2>$null
if (($LASTEXITCODE -ne 0) -or (-not $rdsExists)) {
    Write-Host "Creating RDS instance '$DbInstanceId' (this takes several minutes)..."
    aws rds create-db-instance `
        --db-instance-identifier $DbInstanceId `
        --db-instance-class db.t3.micro `
        --engine postgres `
        --engine-version 15 `
        --master-username $DbUsername `
        --master-user-password $DbPassword `
        --allocated-storage 20 `
        --vpc-security-group-ids $rdsSgId `
        --db-subnet-group-name $subnetGroupName `
        --no-publicly-accessible `
        --backup-retention-period 7 `
        --region $REGION | Out-Null
    Write-Host "RDS create requested. Waiting for instance to be available (can take 5-10 min)..."
    aws rds wait db-instance-available --db-instance-identifier $DbInstanceId --region $REGION
    Write-Host "RDS instance is available." -ForegroundColor Green
} else {
    Write-Host "RDS instance '$DbInstanceId' already exists." -ForegroundColor Yellow
}

$endpoint = aws rds describe-db-instances --db-instance-identifier $DbInstanceId --region $REGION --query "DBInstances[0].Endpoint.Address" --output text
$DATABASE_URL = "postgresql://${DbUsername}:$DbPassword@${endpoint}:5432/postgres"
$DATABASE_URL_INSIGHTSHOP = "postgresql://${DbUsername}:$DbPassword@${endpoint}:5432/${DbName}"
Write-Host ""

# 6. Database: app auto-creates '$DbName' on first run (ensure_postgres_database). No manual psql needed.

# 7. App Runner VPC connector
$connectorArn = $null
$list = aws apprunner list-vpc-connectors --region $REGION --query "VpcConnectors[?VpcConnectorName=='$VpcConnectorName'].VpcConnectorArn" --output text 2>$null
if ($list -and $list -ne "None") { $connectorArn = $list; Write-Host "VPC connector already exists: $connectorArn" -ForegroundColor Yellow }
else {
    $out = aws apprunner create-vpc-connector `
        --vpc-connector-name $VpcConnectorName `
        --subnets $SubnetIds `
        --security-groups $connectorSgId `
        --region $REGION --output json
    $connectorArn = ($out | ConvertFrom-Json).VpcConnector.VpcConnectorArn
    Write-Host "Created VPC connector: $connectorArn" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "========== NEXT STEPS ==========" -ForegroundColor Cyan
Write-Host "1. Add DATABASE_URL to App Runner:" -ForegroundColor White
Write-Host "   App Runner -> insightshop -> Configuration -> Edit -> Environment variables" -ForegroundColor Gray
Write-Host "   Key: DATABASE_URL" -ForegroundColor Gray
Write-Host "   Value: $DATABASE_URL_INSIGHTSHOP" -ForegroundColor Gray
Write-Host "   (Or store in Secrets Manager and add as Runtime environment secret.)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Attach VPC connector to App Runner:" -ForegroundColor White
Write-Host "   Configuration -> Networking -> Outgoing traffic -> VPC connector: $VpcConnectorName" -ForegroundColor Gray
Write-Host "   (ARN: $connectorArn)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Save and redeploy the App Runner service. The app will auto-create the '$DbName' database on first run." -ForegroundColor White
Write-Host ""
Write-Host "DATABASE_URL (for app): $DATABASE_URL_INSIGHTSHOP" -ForegroundColor Green
Write-Host "VpcConnectorArn: $connectorArn" -ForegroundColor Green
