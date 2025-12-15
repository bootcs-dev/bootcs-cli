# bootcs-cli 学员开发环境镜像 (黄金镜像)
#
# 包含所有支持的语言: C, Python, Java
# 与评测环境一致，避免"本地通过、线上失败"问题
#
# 使用方式:
#   docker run --rm -v $(pwd):/workspace ghcr.io/bootcs-cn/cli check cs50/hello
#   docker run --rm -v $(pwd):/workspace ghcr.io/bootcs-cn/cli submit cs50/hello
#
# 支持课程:
#   - CS50 (C, Python)
#   - 数据结构 (C, Python, Java)
#   - 编译器 (C)
#   - 数据库 (Python, Java)
#   - 分布式系统 (Java, Python)

FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/bootcs-cn/bootcs-cli"
LABEL org.opencontainers.image.description="bootcs-cli development environment for students"
LABEL org.opencontainers.image.licenses="MIT"

# ============================================
# 系统基础工具
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# C 语言工具链
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    gcc \
    g++ \
    make \
    gdb \
    valgrind \
    && rm -rf /var/lib/apt/lists/*

# libcs50 (CS50 课程需要)
RUN git clone --depth 1 https://github.com/cs50/libcs50.git /tmp/libcs50 \
    && cd /tmp/libcs50 \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /tmp/libcs50

# ============================================
# Java 工具链
# ============================================
# python:3.11-slim 基于 Debian Bookworm，使用 default-jdk
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    maven \
    && rm -rf /var/lib/apt/lists/*

# 动态获取 JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# ============================================
# Python 已包含在基础镜像中
# ============================================

# ============================================
# 安装 bootcs-cli (从 GitHub 安装)
# ============================================
RUN pip install --no-cache-dir git+https://github.com/bootcs-cn/bootcs-cli.git

# ============================================
# 环境配置
# ============================================
ENV PYTHONUNBUFFERED=1
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /workspace

ENTRYPOINT ["bootcs"]
CMD ["--help"]
