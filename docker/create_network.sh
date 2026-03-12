set -euo pipefail

NETWORK_NAME="my_shared_network"
SUBNET="172.18.0.0/24"
GATEWAY="172.18.0.1"

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