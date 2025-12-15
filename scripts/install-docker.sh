#!/bin/bash
# bootcs-cli Docker 版一键安装脚本
#
# 使用方式:
#   curl -fsSL https://raw.githubusercontent.com/bootcs-cn/bootcs-cli/main/scripts/install-docker.sh | bash
#
# 或本地执行:
#   ./scripts/install-docker.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
IMAGE="${BOOTCS_CLI_IMAGE:-ghcr.io/bootcs-cn/bootcs-cli:latest}"
WRAPPER_NAME="bootcs"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="${HOME}/.bootcs"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║   🚀 bootcs-cli Docker 版安装程序                            ║"
echo "║                                                              ║"
echo "║   支持语言: C, Python, Java                                  ║"
echo "║   支持课程: CS50, 数据结构, 编译器, 数据库, 分布式系统        ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 Docker 是否安装
echo -e "${BLUE}[1/5]${NC} 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo ""
    echo "请先安装 Docker:"
    echo "  - macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  - Linux: https://docs.docker.com/engine/install/"
    echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装${NC}"

# 检查 Docker 是否运行
echo -e "${BLUE}[2/5]${NC} 检查 Docker 服务..."
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    echo "请启动 Docker Desktop 或 Docker 服务"
    exit 1
fi
echo -e "${GREEN}✓ Docker 服务正常${NC}"

# 拉取镜像
echo -e "${BLUE}[3/5]${NC} 拉取 bootcs-cli 镜像..."
echo -e "${YELLOW}   (首次可能需要几分钟，请耐心等待)${NC}"
if docker pull "${IMAGE}"; then
    echo -e "${GREEN}✓ 镜像拉取成功${NC}"
else
    echo -e "${RED}❌ 镜像拉取失败${NC}"
    exit 1
fi

# 创建配置目录
echo -e "${BLUE}[4/5]${NC} 创建配置目录..."
mkdir -p "${CONFIG_DIR}"
echo -e "${GREEN}✓ 配置目录: ${CONFIG_DIR}${NC}"

# 创建 wrapper 脚本
echo -e "${BLUE}[5/5]${NC} 安装 bootcs 命令..."

WRAPPER_SCRIPT='#!/bin/bash
# bootcs-cli Docker wrapper
# 自动生成，请勿手动编辑

IMAGE="ghcr.io/bootcs-cn/bootcs-cli:latest"
CONFIG_DIR="${HOME}/.bootcs"

# 确保配置目录存在
mkdir -p "${CONFIG_DIR}"

# 运行容器
# -v $(pwd):/workspace  - 挂载当前目录为工作目录
# -v ~/.bootcs:/root/.bootcs - 持久化凭证和缓存
# -it - 交互模式 (login 需要)
# --rm - 运行后删除容器

# 检查是否需要交互模式 (login 命令)
if [[ "$1" == "login" ]]; then
    docker run -it --rm \
        -v "$(pwd)":/workspace \
        -v "${CONFIG_DIR}":/root/.bootcs \
        "${IMAGE}" "$@"
else
    docker run --rm \
        -v "$(pwd)":/workspace \
        -v "${CONFIG_DIR}":/root/.bootcs \
        "${IMAGE}" "$@"
fi
'

# 尝试安装到 /usr/local/bin，如果失败则安装到 ~/.local/bin
if [ -w "${INSTALL_DIR}" ]; then
    echo "${WRAPPER_SCRIPT}" > "${INSTALL_DIR}/${WRAPPER_NAME}"
    chmod +x "${INSTALL_DIR}/${WRAPPER_NAME}"
    FINAL_INSTALL_DIR="${INSTALL_DIR}"
else
    # 需要 sudo
    echo -e "${YELLOW}   需要管理员权限安装到 ${INSTALL_DIR}${NC}"
    echo "${WRAPPER_SCRIPT}" | sudo tee "${INSTALL_DIR}/${WRAPPER_NAME}" > /dev/null
    sudo chmod +x "${INSTALL_DIR}/${WRAPPER_NAME}"
    FINAL_INSTALL_DIR="${INSTALL_DIR}"
fi

echo -e "${GREEN}✓ bootcs 命令已安装到 ${FINAL_INSTALL_DIR}/${WRAPPER_NAME}${NC}"

# 验证安装
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 安装完成！${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "使用方式:"
echo ""
echo -e "  ${YELLOW}1. 首次使用，先登录:${NC}"
echo -e "     ${BLUE}bootcs login${NC}"
echo ""
echo -e "  ${YELLOW}2. 检查代码:${NC}"
echo -e "     ${BLUE}cd your-code-directory${NC}"
echo -e "     ${BLUE}bootcs check cs50/hello${NC}"
echo ""
echo -e "  ${YELLOW}3. 提交代码:${NC}"
echo -e "     ${BLUE}bootcs submit cs50/hello${NC}"
echo ""
echo -e "  ${YELLOW}4. 查看帮助:${NC}"
echo -e "     ${BLUE}bootcs --help${NC}"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

# 验证命令可用
if command -v bootcs &> /dev/null; then
    echo -e "${GREEN}✓ 验证成功: bootcs 命令可用${NC}"
    echo ""
    bootcs --version 2>/dev/null || true
else
    echo -e "${YELLOW}⚠ 请重新打开终端或执行: source ~/.zshrc${NC}"
fi
