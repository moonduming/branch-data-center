#!/bin/bash

set -e

# 创建网络（如果不存在）
docker network inspect branch-network >/dev/null 2>&1 || docker network create branch-network

# 删除旧容器（如果存在）
docker rm -f branch-data-center-redis >/dev/null 2>&1 || true
docker rm -f branch-data-center-web >/dev/null 2>&1 || true
docker rm -f branch-data-center-worker >/dev/null 2>&1 || true
docker rm -f branch-data-center-beat >/dev/null 2>&1 || true

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
--env-file .env.local \
--add-host host.docker.internal:host-gateway \
-p 9000:9000 \
branch-data-center:latest \
gunicorn -c gunicorn_conf.py config.asgi:application

echo "Starting Celery Worker..."
docker run -d \
--name branch-data-center-worker \
--network branch-network \
--env-file .env.local \
--add-host host.docker.internal:host-gateway \
branch-data-center:latest \
celery -A config worker -l info

echo "Starting Celery Beat..."
docker run -d \
--name branch-data-center-beat \
--network branch-network \
--env-file .env.local \
--add-host host.docker.internal:host-gateway \
branch-data-center:latest \
celery -A config beat -l info

echo "All services started successfully."

# MNG_ORG_ID + 0100

# docker inspect nginx

# docker exec -it nginx nginx -t 
# docker exec -it nginx nginx -s reload

# -x "*.DS_Store"
# ALTER TABLE data_import_log
# ADD COLUMN run_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '运行次数';

zip -r project.zip . -x ".git/*" "__pycache__/*" "*.pyc" "venv/*" ".env" ".DS_Store"
