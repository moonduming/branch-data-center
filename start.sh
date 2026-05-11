#!/bin/bash

set -e

# echo "Starting branch-data-center services..."

# 删除旧容器（如果存在）
docker rm -f branch-data-center-redis >/dev/null 2>&1 || true
docker rm -f branch-data-center-web >/dev/null 2>&1 || true
docker rm -f branch-data-center-worker >/dev/null 2>&1 || true
docker rm -f branch-data-center-beat >/dev/null 2>&1 || true

# 加载镜像（如果存在 images.tar）
if [ -f "images.tar" ]; then
  echo "images.tar detected, removing old images and loading new ones..."

  # 删除旧镜像（如果存在）
  docker rmi -f redis:7-alpine >/dev/null 2>&1 || true
  docker rmi -f branch-data-center:latest >/dev/null 2>&1 || true

  # 加载新镜像
  docker load -i images.tar
fi


# 创建网络（如果不存在）
docker network inspect branch-network >/dev/null 2>&1 || docker network create branch-network

# 将已存在的 nginx 容器加入网络（如果存在且未加入）
if docker ps -a --format '{{.Names}}' | grep -q '^nginx$'; then
  docker network connect branch-network nginx >/dev/null 2>&1 || true
fi

echo "Starting Redis..."
docker run -d \
--name branch-data-center-redis \
--network branch-network \
-p 6379:6379 \
redis:7-alpine

echo "Starting Django Web..."
docker run -d \
--name branch-data-center-web \
--network branch-network \
--env-file .env \
--add-host host.docker.internal:host-gateway \
--privileged \
-p 9000:9000 \
branch-data-center:latest \
gunicorn -c gunicorn_conf.py config.asgi:application

echo "Starting Celery Worker..."
docker run -d \
--name branch-data-center-worker \
--network branch-network \
--env-file .env \
--add-host host.docker.internal:host-gateway \
--privileged \
-v /home/shenzhen_data_ftp/shenzhen_data:/app/shenzhen_data \
branch-data-center:latest \
celery -A config worker -l info

echo "Starting Celery Beat..."
docker run -d \
--name branch-data-center-beat \
--network branch-network \
--env-file .env \
--add-host host.docker.internal:host-gateway \
--privileged \
branch-data-center:latest \
celery -A config beat -l info


echo "All services started successfully."

echo "Starting host Flask service as specified user..."

# 指定脚本、配置和日志路径（按需修改）
SCRIPT_DIR="$(pwd)"
SOURCE_SCRIPT_PATH="$SCRIPT_DIR/dbtool_service.py"
SOURCE_CONFIG_PATH="$SCRIPT_DIR/config.json"
LOG_FILE="$SCRIPT_DIR/dbtool_service.log"

# 先杀掉已有的 dbtool_service 进程（如果存在）
PIDS=$(ps -ef | grep dbtool_service.py | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
  echo "Found existing dbtool_service processes: $PIDS, killing..."
  kill -9 $PIDS >/dev/null 2>&1 || true
  sleep 1
fi

cd "$SCRIPT_DIR"
nohup python3 "$SOURCE_SCRIPT_PATH" >> "$LOG_FILE" 2>&1 &
echo "Host Flask service started. Log file: $LOG_FILE"
