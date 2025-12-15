#!/bin/bash
# bootcs-cli Docker wrapper
#
# 这个脚本让你可以像使用本地安装的 bootcs 一样使用 Docker 版本
# 凭证和缓存会自动持久化到 ~/.bootcs 目录
#
# 安装方式:
#   sudo cp scripts/bootcs-wrapper.sh /usr/local/bin/bootcs
#   sudo chmod +x /usr/local/bin/bootcs
#
# 或者添加 alias 到 ~/.zshrc 或 ~/.bashrc:
#   alias bootcs='/path/to/bootcs-wrapper.sh'

set -e

# 配置
IMAGE="${BOOTCS_CLI_IMAGE:-ghcr.io/bootcs-cn/bootcs-cli:latest}"
CONFIG_DIR="${HOME}/.bootcs"

# 确保配置目录存在
mkdir -p "${CONFIG_DIR}"

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH" >&2
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker." >&2
    exit 1
fi

# 检查镜像是否存在，如果不存在则自动拉取
if ! docker image inspect "${IMAGE}" &> /dev/null; then
    echo "First run: pulling bootcs-cli image..." >&2
    docker pull "${IMAGE}"
fi

# 运行容器
# 参数说明:
#   -v $(pwd):/workspace     挂载当前目录为工作目录
#   -v ~/.bootcs:/root/.bootcs  持久化凭证和缓存
#   --rm                     运行后删除容器
#   -it                      交互模式 (login 需要)

# 根据命令决定是否需要交互模式
case "${1:-}" in
    login)
        # login 需要交互输入
        exec docker run -it --rm \
            -v "$(pwd)":/workspace \
            -v "${CONFIG_DIR}":/root/.bootcs \
            "${IMAGE}" "$@"
        ;;
    *)
        # 其他命令不需要交互
        exec docker run --rm \
            -v "$(pwd)":/workspace \
            -v "${CONFIG_DIR}":/root/.bootcs \
            "${IMAGE}" "$@"
        ;;
esac
