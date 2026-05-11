bind = "0.0.0.0:9000"

# 先保守一点
workers = 2

# ASGI 必须用这个 worker
worker_class = "uvicorn.workers.UvicornWorker"

threads = 2

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 超时
timeout = 60
keepalive = 5

# 可选：防止长时间运行后资源累积
max_requests = 1000
max_requests_jitter = 50

# 先不要预加载，避免 fork/初始化带来额外问题
preload_app = False

# 某些环境下比 /tmp 更稳
worker_tmp_dir = "/dev/shm"