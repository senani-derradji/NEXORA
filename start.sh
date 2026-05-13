#!/bin/bash

# ============================================
# Smart Apiary - Automated Docker Setup Script
# ============================================

set -e

# Configuration
PROFILE="${1:-vlab}"
COMPOSE_FILE="docker_compose_full.yml"
TELEGRAM_ENV_FILE="core/configs/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}Using profile: $PROFILE${NC}"
echo ""

# Function to check if token is valid
check_influxdb_token() {
    local token="$1"
    curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Token $token" "http://localhost:8086/api/v2/orgs" 2>/dev/null
}

# Clean environment
echo -e "${CYAN}Cleaning environment...${NC}"
docker compose -f $COMPOSE_FILE --profile $PROFILE down -v 2>/dev/null || true
echo ""

# Start InfluxDB
echo -e "${CYAN}Starting InfluxDB...${NC}"
docker compose -f $COMPOSE_FILE --profile $PROFILE up -d influxdb

echo -n "Waiting for InfluxDB"
while true; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' influxdb 2>/dev/null || echo "starting")
    echo -n "."
    if [ "$STATUS" = "healthy" ]; then
        break
    fi
    sleep 2
done
echo ""
echo -e "${GREEN}✓ InfluxDB is healthy${NC}"
echo ""

# Get or generate InfluxDB token
TOKEN=""

# Try to get existing token from environment
if [ -n "$INFLUXDB_TOKEN" ]; then
    TOKEN="$INFLUXDB_TOKEN"
    echo -e "${GREEN}✓ Using token from environment variable${NC}"
fi

# Try to get token from config file if exists
if [ -z "$TOKEN" ] && [ -f "backend/.env" ]; then
    TOKEN=$(grep "^INFLUXDB_INIT_ADMIN_TOKEN=" "backend/.env" | cut -d'=' -f2 | tr -d '\n\r')
    if [ -n "$TOKEN" ]; then
        echo -e "${GREEN}✓ Using token from existing .env file${NC}"
    fi
fi

# If still no token, prompt user
if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  INFLUXDB TOKEN REQUIRED${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo -e "${GREEN}  1. Open: http://localhost:8086${NC}"
    echo -e "${WHITE}  2. Login: admin / admin123${NC}"
    echo -e "${WHITE}  3. Go to Data > API Tokens${NC}"
    echo -e "${WHITE}  4. Copy the token${NC}"
    echo ""
    read -p "$(echo -e ${CYAN}Paste the token: ${NC})" TOKEN

    if [ -z "$TOKEN" ]; then
        echo -e "${RED}Error: Token cannot be empty!${NC}"
        exit 1
    fi
fi

# Validate token
echo -e "${CYAN}Validating token...${NC}"
HTTP_CODE=$(check_influxdb_token "$TOKEN")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Token is valid${NC}"
else
    echo -e "${YELLOW}⚠ Token validation returned HTTP $HTTP_CODE${NC}"
    echo -e "${YELLOW}  The token might still work, continuing...${NC}"
fi
echo ""

# Get Telegram credentials
TELEGRAM_CHAT_ID=""
TELEGRAM_BOT_TOKEN=""

# Try environment variables
if [ -n "$TELEGRAM_CHAT_ID" ] && [ "$TELEGRAM_CHAT_ID" != "CHAT" ]; then
    TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
    echo -e "${GREEN}✓ Using TELEGRAM_CHAT_ID from environment${NC}"
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ "$TELEGRAM_BOT_TOKEN" != "BOT" ]; then
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
    echo -e "${GREEN}✓ Using TELEGRAM_BOT_TOKEN from environment${NC}"
fi

# Try existing .env file
if [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f "$TELEGRAM_ENV_FILE" ]; then
        if [ -z "$TELEGRAM_CHAT_ID" ]; then
            EXISTING_CHAT=$(grep "^TELEGRAM_CHAT_ID=" "$TELEGRAM_ENV_FILE" | cut -d'=' -f2 | tr -d '\n\r')
            if [ -n "$EXISTING_CHAT" ] && [ "$EXISTING_CHAT" != "CHAT" ]; then
                TELEGRAM_CHAT_ID="$EXISTING_CHAT"
                echo -e "${GREEN}✓ Using TELEGRAM_CHAT_ID from existing .env${NC}"
            fi
        fi

        if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
            EXISTING_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$TELEGRAM_ENV_FILE" | cut -d'=' -f2 | tr -d '\n\r')
            if [ -n "$EXISTING_TOKEN" ] && [ "$EXISTING_TOKEN" != "BOT" ]; then
                TELEGRAM_BOT_TOKEN="$EXISTING_TOKEN"
                echo -e "${GREEN}✓ Using TELEGRAM_BOT_TOKEN from existing .env${NC}"
            fi
        fi
    fi
fi

# Prompt for missing credentials
if [ -z "$TELEGRAM_CHAT_ID" ] || [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  TELEGRAM SETUP REQUIRED${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""

    if [ -z "$TELEGRAM_CHAT_ID" ]; then
        read -p "$(echo -e ${CYAN}Telegram Chat ID: ${NC})" TELEGRAM_CHAT_ID
        if [ -z "$TELEGRAM_CHAT_ID" ]; then
            echo -e "${RED}Error: Telegram chat ID cannot be empty!${NC}"
            exit 1
        fi
    fi

    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        read -p "$(echo -e ${CYAN}Telegram Bot Token: ${NC})" TELEGRAM_BOT_TOKEN
        if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
            echo -e "${RED}Error: Telegram bot token cannot be empty!${NC}"
            exit 1
        fi
    fi
fi
echo ""

# Create directory structure if needed
echo -e "${CYAN}Creating directory structure...${NC}"
mkdir -p backend core/configs core/time_series/config collectors/config/db_config frontend docker
echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Create .env files
echo -e "${CYAN}Creating .env files...${NC}"

# Main .env
cat > .env << EOF
POSTGRES_USER=nexorauser
POSTGRES_PASSWORD=nexorapass
POSTGRES_DB=nexoradb

INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=admin123
INFLUXDB_DB=mydb
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test
INFLUXDB_INIT_ADMIN_TOKEN=$TOKEN

VITE_API_BASE_URL=/

DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
EOF

# Backend .env
cat > backend/.env << EOF
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_URL=http://influxdb:8086
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=dr_test

INFLUXDB_INIT_ADMIN_TOKEN=$TOKEN
EOF

# Core configs .env
cat > core/configs/.env << EOF
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb

INFLUXDB_INIT_ADMIN_TOKEN=$TOKEN
INFLUXDB_URL=http://influxdb:8086
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
EOF

# Core time series .env
cat > core/time_series/config/.env << EOF
INFLUXDB_INIT_ADMIN_TOKEN=$TOKEN
TSBS_ORGANIZATION=myorg
TSBS_BUCKET=dr_test
TSBS_URL=http://influxdb:8086
EOF

# Collectors .env
cat > collectors/config/db_config/.env << EOF
DATABASE_URL=postgresql+psycopg2://nexorauser:nexorapass@postgres:5432/nexoradb
EOF

# Frontend .env
cat > frontend/.env << EOF
VITE_API_BASE_URL=http://backend:8000
EOF

# Docker .env
cat > docker/.env << EOF
# Postgres
POSTGRES_USER=nexorauser
POSTGRES_PASSWORD=nexorapass
POSTGRES_DB=nexoradb

# Network
NETWORK_NAME=my_shared_network
SUBNET=172.18.0.0/24
GATEWAY=172.18.0.1
EOF

# Security .env
cat > backend/security/.env << EOF
SECRET_KEY=secret_test
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
EOF

echo -e "${GREEN}✓ All .env files created${NC}"
echo ""

# Start services
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  SETUP COMPLETE!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Services are starting up...${NC}"
echo ""
echo -e "${CYAN}  Frontend:  http://localhost:3000${NC}"
echo -e "${CYAN}  Backend:   http://localhost:8000${NC}"
echo -e "${CYAN}  InfluxDB:  http://localhost:8086${NC}"
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  SHOWING LOGS${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop viewing logs${NC}"
echo ""

# Start full stack
docker compose -f $COMPOSE_FILE --profile $PROFILE up --build