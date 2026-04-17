#!/bin/bash

set -e

APP_NAME="mailgw"

BACKEND_DIR="."
VENV_DIR="$BACKEND_DIR/venv"

API_SCREEN_NAME="${APP_NAME}_api"
WORKER_SCREEN_NAME="${APP_NAME}_worker"
NGINX_CONF_SOURCE="$PROJECT_DIR/nginx.conf"
NGINX_CONF_TARGET_DIR="/etc/nginx/includes/"
API_PORT=8067

kill_screen() {
    local name=$1
    if screen -list | grep -q "$name"; then
        echo "Stopping screen: $name"
        screen -S "$name" -X quit || true
    fi
}

echo "Starting deploy..."

kill_screen "$API_SCREEN_NAME"
kill_screen "$WORKER_SCREEN_NAME"

cd "$BACKEND_DIR" || { echo "Directory not found: $BACKEND_DIR"; exit 1; }

if [ ! -d "$VENV_DIR" ]; then
    echo "Virtualenv not found: $VENV_DIR"
    exit 1
fi

source "$VENV_DIR/bin/activate" || { echo "Failed to activate venv"; exit 1; }

echo "Installing dependencies..."
pip install -r requirements.txt
echo "Nginx..."

if [ ! -f "$NGINX_CONF_SOURCE" ]; then
echo "Error: $NGINX_CONF_SOURCE nginx config file not found."
exit 1
fi

sudo cp "$NGINX_CONF_SOURCE" "$NGINX_CONF_TARGET_DIR" || { echo "Nginx config copy error."; exit 1; }

echo "Restarting Nginx..."
sudo nginx -t || { echo "Nginx config error."; exit 1; }
sudo nginx -s reload || { echo "Nginx reload error."; exit 1; }

echo "Starting API in screen: $API_SCREEN_NAME"
screen -dmS "$API_SCREEN_NAME" bash -c "
cd \"$BACKEND_DIR\" &&
source \"$VENV_DIR/bin/activate\" &&
uvicorn app.main:app --host 0.0.0.0 --port $API_PORT
"

echo "Starting Celery worker in screen: $WORKER_SCREEN_NAME"
screen -dmS "$WORKER_SCREEN_NAME" bash -c "
cd \"$BACKEND_DIR\" &&
source \"$VENV_DIR/bin/activate\" &&
celery -A app.tasks.celery_app worker -Q mail --loglevel=info --concurrency=1
"

sleep 2

echo "Checking processes..."

if screen -list | grep -q "$API_SCREEN_NAME" && \
   screen -list | grep -q "$WORKER_SCREEN_NAME"; then

    echo "Deploy successful"
    echo "API screen: $API_SCREEN_NAME"
    echo "Worker screen: $WORKER_SCREEN_NAME"
    echo "URL: http://0.0.0.0:$API_PORT"

else
    echo "Error: one or more processes failed to start"
    exit 1
fi

deactivate