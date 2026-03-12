@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: docker/create_network.bat
::
:: Creates the NEXORA shared overlay network if it does not already exist.
:: Only needed when you want to pre-create the network manually.
:: docker_compose_full.yml creates it automatically.
:: ─────────────────────────────────────────────────────────────────────────────

set NETWORK_NAME=my_shared_network
set SUBNET=172.18.0.0/24
set GATEWAY=172.18.0.1

docker network inspect %NETWORK_NAME% >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [network] '%NETWORK_NAME%' already exists -- skipping creation.
) else (
    echo [network] Creating '%NETWORK_NAME%' (%SUBNET%) ...
    docker network create --driver bridge --subnet %SUBNET% --gateway %GATEWAY% %NETWORK_NAME%
    echo [network] '%NETWORK_NAME%' created successfully.
)
