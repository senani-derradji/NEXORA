param(
    [string]$Profile = "vlab"
)

$ComposeFile = "docker_compose_full.yml"
$TelegramEnvFile = "core/configs/.env"

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
INFLUXDB_INIT_ADMIN_TOKEN=placeholder

VITE_API_BASE_URL=/

DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
"@

$backendEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test

INFLUXDB_INIT_ADMIN_TOKEN=placeholder
"@

$coreConfigsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_INIT_ADMIN_TOKEN=placeholder
INFLUXDB_URL=http://influxdb:8086
TELEGRAM_BOT_TOKEN=BOT
TELEGRAM_CHAT_ID=CHAT
"@

$coreTimeSeriesEnvContent = @"
INFLUXDB_INIT_ADMIN_TOKEN=placeholder
TSBS_ORGANIZATION=myorg
TSBS_BUCKET=dr_test
TSBS_URL=http://influxdb:8086
"@

$collectorsEnvContent = @"
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
"@

$frontendEnvContent = @"
VITE_API_BASE_URL=http://backend:8000
"@

$dockerEnvContent = @"
# Postgres
POSTGRES_USER=nexorauser
POSTGRES_PASSWORD=nexorapass
POSTGRES_DB=nexoradb

# Network
NETWORK_NAME=my_shared_network
SUBNET=172.18.0.0/24
GATEWAY=172.18.0.1
"@

$SecurityEnvContent = @"
SECRET_KEY=secret_test
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
"@


$envFiles = @{
    ".env" = $envContent
    "backend/.env" = $backendEnvContent
    "core/configs/.env" = $coreConfigsEnvContent
    "core/time_series/config/.env" = $coreTimeSeriesEnvContent
    "collectors/config/db_config/.env" = $collectorsEnvContent
    "frontend/.env" = $frontendEnvContent
    "docker/.env" = $dockerEnvContent
    "backend/security/.env" = $SecurityEnvContent
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


# ── InfluxDB Token ────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INFLUXDB TOKEN REQUIRED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Open: http://localhost:8086" -ForegroundColor Green
Write-Host "  2. Login: admin / admin123" -ForegroundColor White
Write-Host "  3. Go to Data > API Tokens" -ForegroundColor White
Write-Host "  4. Copy the token (or generate a new one)" -ForegroundColor White
Write-Host ""

$token = Read-Host "Paste the token here"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Error: Token cannot be empty!" -ForegroundColor Red
    exit 1
}

Write-Host "InfluxDB token retrieved successfully." -ForegroundColor Green

# Update .env files with InfluxDB token
$envPath = "core/configs/.env"
$envContent = Get-Content $envPath -Raw
$envContent = $envContent -replace "INFLUXDB_INIT_ADMIN_TOKEN=.*", "INFLUXDB_INIT_ADMIN_TOKEN=$token"
Set-Content -Path $envPath -Value $envContent
Write-Host "Updated core/configs/.env with InfluxDB token." -ForegroundColor Green

# Also update core/time_series/config/.env
$tsEnvPath = "core/time_series/config/.env"
$tsEnvContent = Get-Content $tsEnvPath -Raw
$tsEnvContent = $tsEnvContent -replace "INFLUXDB_INIT_ADMIN_TOKEN=.*", "INFLUXDB_INIT_ADMIN_TOKEN=$token"
Set-Content -Path $tsEnvPath -Value $tsEnvContent
Write-Host "Updated core/time_series/config/.env with InfluxDB token." -ForegroundColor Green


# ── Telegram Credentials ──────────────────────────────────────────────
$telegramChatID = $null
$telegramBotToken = $null

# Check environment variables first
$envChatID = [System.Environment]::GetEnvironmentVariable("TELEGRAM_CHAT_ID")
$envBotToken = [System.Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN")

if (-not [string]::IsNullOrWhiteSpace($envChatID) -and $envChatID -ne "CHAT") {
    $telegramChatID = $envChatID
}
if (-not [string]::IsNullOrWhiteSpace($envBotToken) -and $envBotToken -ne "BOT") {
    $telegramBotToken = $envBotToken
}

# If env vars didn't provide valid values, check existing .env file
if ($null -ne $telegramChatID -and $null -ne $telegramBotToken) {
    Write-Host "Found Telegram credentials in environment variables." -ForegroundColor Green
} elseif (Test-Path $TelegramEnvFile) {
    $existingContent = Get-Content $TelegramEnvFile -Raw
    if ($null -eq $telegramChatID -and $existingContent -match "TELEGRAM_CHAT_ID=(.+)") {
        $val = $Matches[1].Trim()
        if ($val -ne "CHAT" -and -not [string]::IsNullOrWhiteSpace($val)) {
            $telegramChatID = $val
        }
    }
    if ($null -eq $telegramBotToken -and $existingContent -match "TELEGRAM_BOT_TOKEN=(.+)") {
        $val = $Matches[1].Trim()
        if ($val -ne "BOT" -and -not [string]::IsNullOrWhiteSpace($val)) {
            $telegramBotToken = $val
        }
    }
    if ($null -ne $telegramChatID -and $null -ne $telegramBotToken) {
        Write-Host "Found saved Telegram credentials in .env file." -ForegroundColor Green
    }
}

# Prompt user for any missing credentials
if ($null -eq $telegramChatID -or $null -eq $telegramBotToken) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  TELEGRAM SETUP REQUIRED" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    if ($null -eq $telegramChatID) {
        $telegramChatID = Read-Host "Paste the Telegram chat ID here"
        if ([string]::IsNullOrWhiteSpace($telegramChatID)) {
            Write-Host "Error: Telegram chat ID cannot be empty!" -ForegroundColor Red
            exit 1
        }
    }

    if ($null -eq $telegramBotToken) {
        $telegramBotToken = Read-Host "Paste the Telegram bot token here"
        if ([string]::IsNullOrWhiteSpace($telegramBotToken)) {
            Write-Host "Error: Telegram bot token cannot be empty!" -ForegroundColor Red
            exit 1
        }
    }
}

# Update .env file with Telegram credentials
if ($null -ne $telegramChatID -and $null -ne $telegramBotToken) {
    $envPath = "core/configs/.env"
    $envContent = Get-Content $envPath -Raw
    $envContent = $envContent -replace "TELEGRAM_BOT_TOKEN=.*", "TELEGRAM_BOT_TOKEN=$telegramBotToken"
    $envContent = $envContent -replace "TELEGRAM_CHAT_ID=.*", "TELEGRAM_CHAT_ID=$telegramChatID"
    Set-Content -Path $envPath -Value $envContent
    Write-Host "Updated .env file with Telegram credentials." -ForegroundColor Green
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
