# branch-data-center
银行基础数据管理平台

## 部署步骤

1. 下载 Redis 镜像：

   ```bash
   docker pull redis:7-alpine
   ```

2. 在项目根目录构建后端镜像：

   ```bash
   docker build -t branch-data-center:latest .
   ```

3. 打包两个镜像，输出文件名必须为 `images.tar`：

   ```bash
   docker save -o images.tar redis:7-alpine branch-data-center:latest
   ```

4. 在部署环境执行 `start.sh` 部署脚本。

   注意：`dbtool_service.py`、`config.json`、`.env` 文件需要与执行脚本处于同级目录，三个文件均可在项目根目录下找到。
