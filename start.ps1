param(
    [string]$Profile = "vlab"
)

$ComposeFile = "docker_compose_full.yml"

Write-Host "Using profile: $Profile"

Write-Host "Cleaning environment..."
docker compose -f $ComposeFile --profile $Profile down -v | Out-Null

Write-Host "Creating .env files..."

$envContent = @"
POSTGRES_USER=nexorauser
POSTGRES_PASSWORD=nexorapass
POSTGRES_DB=nexoradb

INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin123
INFLUXDB_DB=mydb
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test
INFLUXDB_INIT_ADMIN_TOKEN=Token

VITE_API_BASE_URL=/

DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
"@

$backendEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test

INFLUXDB_INIT_ADMIN_TOKEN=Token
"@

$coreConfigsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_INIT_ADMIN_TOKEN=Token
INFLUXDB_URL=http://influxdb:8086
TELEGRAM_BOT_TOKEN=BOT
TELEGRAM_CHAT_ID=CHAT
"@

$coreTimeSeriesEnvContent = @"
INFLUXDB_INIT_ADMIN_TOKEN=Token
TSBS_ORGANIZATION=myorg
TSBS_BUCKET=dr_test
TSBS_URL=http://influxdb:8086
"@

$collectorsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
"@

# Frontend .env content
$frontendEnvContent = @"
VITE_API_BASE_URL=http://backend:8000
"@

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

Write-Host "Starting InfluxDB..."
docker compose -f $ComposeFile --profile $Profile up -d influxdb | Out-Null

Write-Host "Waiting for InfluxDB to start..."

do {
    Start-Sleep -Seconds 2
    $status = docker inspect --format='{{.State.Health.Status}}' influxdb 2>$null
    Write-Host "Status: $status"
} while ($status -ne "healthy")

Write-Host "InfluxDB is ready!"

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

$token = Read-Host "Paste the InfluxDB token here"
$telegramChatID = Read-Host "Paste the Telegram chat ID here"
$telegramBotToken = Read-Host "Paste the Telegram bot token here"


if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Error: Token cannot be empty!" -ForegroundColor Red
    exit 1
}
if ([string]::IsNullOrWhiteSpace($telegramChatID)) {
    Write-Host "Error: Telegram chat ID cannot be empty!" -ForegroundColor Red
    exit 1
}
if ([string]::IsNullOrWhiteSpace($telegramBotToken)) {
    Write-Host "Error: Telegram bot token cannot be empty!" -ForegroundColor Red
    exit 1
}

write-host "========================================"
Write-Host ""
Write-Host "Token received: $token" -ForegroundColor Green
Write-Host "Telegram chat ID received: $telegramChatID" -ForegroundColor Green
Write-Host "Telegram bot token received: $telegramBotToken" -ForegroundColor Green
Write-Host ""
Write-Host "========================================"

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

        if ($txt -match "INFLUXDB_INIT_ADMIN_TOKEN=.*") {
            $txt = $txt -replace "INFLUXDB_INIT_ADMIN_TOKEN=.*\r?\n?", ""
        }
        if ($txt -match "TELEGRAM_CHAT_ID=.*") {
            $txt = $txt -replace "TELEGRAM_CHAT_ID=.*\r?\n?", ""
        }
        if ($txt -match "TELEGRAM_BOT_TOKEN=.*") {
            $txt = $txt -replace "TELEGRAM_BOT_TOKEN=.*\r?\n?", ""
        }


        $txt += "`r`nINFLUXDB_INIT_ADMIN_TOKEN=$token"
        $txt += "`r`nTELEGRAM_CHAT_ID=$telegramChatID"
        $txt += "`r`nTELEGRAM_BOT_TOKEN=$telegramBotToken"

        Set-Content $f $txt
        Write-Host "Updated $f"
    }
}

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

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  SHOWING LOGS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop viewing logs" -ForegroundColor Yellow
Write-Host ""

Write-Host ""
Write-Host "Starting full stack..."

docker compose -f $ComposeFile --profile $Profile up --build