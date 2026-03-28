@echo off

set "SCRIPT_DIR=%~dp0"

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /v "#" "%SCRIPT_DIR%.env"`) do (
    set "%%A=%%B"
)

docker network inspect %NETWORK_NAME% >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [network] '%NETWORK_NAME%' already exists -- skipping creation.
) else (
    echo [network] Creating '%NETWORK_NAME%' (%SUBNET%) ...
    docker network create --driver bridge --subnet %SUBNET% --gateway %GATEWAY% %NETWORK_NAME%
    echo [network] '%NETWORK_NAME%' created successfully.
)
