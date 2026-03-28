set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
. "$SCRIPT_DIR/.env"
set +a

if docker network inspect "$NETWORK_NAME" > /dev/null 2>&1; then
    echo "[network] '$NETWORK_NAME' already exists — skipping creation."
else
    echo "[network] Creating '$NETWORK_NAME' ($SUBNET) ..."
    docker network create \
        --driver bridge \
        --subnet "$SUBNET" \
        --gateway "$GATEWAY" \
        "$NETWORK_NAME"
    echo "[network] '$NETWORK_NAME' created successfully."
fi
