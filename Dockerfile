# bootcs-cli Docker Image
# 用于本地自测和 GitHub Actions 评测

FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/bootcs-cn/bootcs-cli"
LABEL org.opencontainers.image.description="BootCS CLI for code checking and evaluation"
LABEL org.opencontainers.image.licenses="GPL-3.0"

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    curl \
    gcc \
    git \
    make \
    valgrind \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY pyproject.toml README.md LICENSE ./
COPY bootcs/ ./bootcs/

# 安装 bootcs
RUN pip install --no-cache-dir -e .

# 创建工作目录
WORKDIR /workspace

# 入口点
ENTRYPOINT ["python", "-m", "bootcs"]
CMD ["--help"]
