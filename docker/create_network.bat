@echo off

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
