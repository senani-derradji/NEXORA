param(
    [string]$Profile = "vlab"
)

$ComposeFile = "docker_compose_full.yml"

Write-Host "Using profile: $Profile"

# ---------------- CLEAN ----------------
Write-Host "Cleaning environment..."
docker compose -f $ComposeFile --profile $Profile down -v | Out-Null

# ---------------- ENV FILES SETUP ----------------
Write-Host "Creating .env files..."

# Define all environment variables
$envContent = @"
# PostgreSQL Configuration
POSTGRES_USER=nexorauser
POSTGRES_PASSWORD=nexorapass
POSTGRES_DB=nexoradb

# InfluxDB Configuration
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin123
INFLUXDB_DB=mydb
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test
INFLUXDB_INIT_ADMIN_TOKEN=Token

# Frontend Configuration
VITE_API_BASE_URL=/

# Database URL
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
"@

# Backend .env content
$backendEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

# InfluxDB connection (for querying metrics)
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test

INFLUXDB_INIT_ADMIN_TOKEN=Token
"@

# Core configs .env content
$coreConfigsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_INIT_ADMIN_TOKEN=Token
"@

# Core time_series config .env content
$coreTimeSeriesEnvContent = @"
INFLUXDB_INIT_ADMIN_TOKEN=Token
TSBS_ORGANIZATION=myorg
TSBS_BUCKET=dr_test
TSBS_URL=http://influxdb:8086
"@

# Collectors db_config .env content
$collectorsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_INIT_ADMIN_TOKEN=Token
"@

# Frontend .env content
$frontendEnvContent = @"
# NEXORA Frontend Environment Variables
# For Docker builds: use relative path (nginx proxies to backend)
VITE_API_BASE_URL=http://backend:8000

INFLUXDB_INIT_ADMIN_TOKEN=Token
"@

# Create .env files
$envFiles = @{
    ".env" = $envContent
    "backend/.env" = $backendEnvContent
    "core/configs/.env" = $coreConfigsEnvContent
    "core/time_series/config/.env" = $coreTimeSeriesEnvContent
    "collectors/config/db_config/.env" = $collectorsEnvContent
    "frontend/.env" = $frontendEnvContent
}

foreach ($file in $envFiles.Keys) {
    $directory = Split-Path $file -Parent
    if ($directory -and -not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    Set-Content -Path $file -Value $envFiles[$file]
    Write-Host "Created $file"
}

# ---------------- START INFLUX ----------------
Write-Host "Starting InfluxDB..."
docker compose -f $ComposeFile --profile $Profile up -d influxdb | Out-Null

Write-Host "Waiting for InfluxDB to start..."

do {
    Start-Sleep -Seconds 2
    $status = docker inspect --format='{{.State.Health.Status}}' influxdb 2>$null
    Write-Host "Status: $status"
} while ($status -ne "healthy")

Write-Host "InfluxDB is ready!"

# ---------------- MANUAL TOKEN INPUT ----------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INFLUXDB SETUP REQUIRED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please open InfluxDB in your browser and create a token:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  URL: http://localhost:8086" -ForegroundColor Green
Write-Host ""
Write-Host "  Login credentials:" -ForegroundColor Yellow
Write-Host "    Username: admin" -ForegroundColor White
Write-Host "    Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "  Steps to create token:" -ForegroundColor Yellow
Write-Host "    1. Log in to InfluxDB" -ForegroundColor White
Write-Host "    2. Go to 'Data' > 'API Tokens'" -ForegroundColor White
Write-Host "    3. Click 'Generate API Token'" -ForegroundColor White
Write-Host "    4. Select 'All Access Token'" -ForegroundColor White
Write-Host "    5. Click 'Save'" -ForegroundColor White
Write-Host "    6. Copy the generated token" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Wait for user to input the token
$token = Read-Host "Paste the InfluxDB token here"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Error: Token cannot be empty!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Token received: $token" -ForegroundColor Green

# ---------------- ENV UPDATE ----------------
Write-Host "Updating .env files with token..."

$files = @(
".env",
"backend/.env",
"core/configs/.env",
"core/time_series/config/.env",
"collectors/config/db_config/.env",
"frontend/.env"
)

foreach ($f in $files) {

    if (Test-Path $f) {

        $txt = Get-Content $f -Raw

        # Remove existing INFLUXDB_INIT_ADMIN_TOKEN line if it exists
        if ($txt -match "INFLUXDB_INIT_ADMIN_TOKEN=.*") {
            $txt = $txt -replace "INFLUXDB_INIT_ADMIN_TOKEN=.*\r?\n?", ""
        }

        # Add new token value
        $txt += "`r`nINFLUXDB_INIT_ADMIN_TOKEN=$token"

        Set-Content $f $txt
        Write-Host "Updated $f"
    }
}

# ---------------- RESTART CORE SERVICE ----------------
Write-Host ""
Write-Host "Restarting core service to pick up new token..."

# Restart core service to pick up new .env files
docker compose -f $ComposeFile --profile $Profile restart core

Write-Host "Core service restarted!"

# ---------------- START FULL STACK ----------------
Write-Host ""
Write-Host "Starting full stack..."
docker compose -f $ComposeFile --profile $Profile up -d

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are starting up..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  InfluxDB:  http://localhost:8086" -ForegroundColor Cyan
Write-Host ""

# ---------------- SHOW LOGS ----------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  SHOWING LOGS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop viewing logs" -ForegroundColor Yellow
Write-Host ""

# Show logs for all services
docker compose -f $ComposeFile --profile $Profile logs -f
