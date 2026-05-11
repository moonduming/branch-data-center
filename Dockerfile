# syntax=docker/dockerfile:1

# =========================
# Builder stage
# - 安装编译依赖
# - 构建 Python 虚拟环境并安装 requirements
# =========================
FROM arm64v8/python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.test

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -r requirements.txt


# =========================
# Runtime stage
# - 只保留运行所需内容
# - 使用 gunicorn 启动
# =========================
FROM arm64v8/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.test \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# mysqlclient 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    vim \
    procps \
    net-tools \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY . .

EXPOSE 9000

# CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "9000", "--workers", "2"]
