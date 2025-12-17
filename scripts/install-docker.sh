#!/bin/bash
# bootcs-cli Docker 版一键安装脚本
#
# 使用方式:
#   curl -fsSL https://raw.githubusercontent.com/bootcs-dev/bootcs-cli/main/scripts/install-docker.sh | bash
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
IMAGE="${BOOTCS_CLI_IMAGE:-ghcr.io/bootcs-dev/bootcs-cli:latest}"
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
echo -e "${BLUE}[4/6]${NC} 创建配置目录..."
mkdir -p "${CONFIG_DIR}"
echo -e "${GREEN}✓ 配置目录: ${CONFIG_DIR}${NC}"

# 检查是否已安装本地版 bootcs
echo -e "${BLUE}[5/6]${NC} 检查已有安装..."
EXISTING_BOOTCS=$(command -v bootcs 2>/dev/null || true)
if [ -n "$EXISTING_BOOTCS" ]; then
    # 检查是否是 Docker wrapper（包含 "docker run"）
    if grep -q "docker run" "$EXISTING_BOOTCS" 2>/dev/null; then
        echo -e "${YELLOW}   检测到已安装 Docker 版，将更新...${NC}"
    else
        echo -e "${YELLOW}⚠ 检测到已安装本地版 bootcs: ${EXISTING_BOOTCS}${NC}"
        echo ""
        echo "  本地版和 Docker 版会冲突。建议："
        echo "  1. 使用 Docker 版（推荐，环境一致）: 继续安装"
        echo "  2. 保留本地版: 按 Ctrl+C 取消"
        echo ""
        read -p "是否用 Docker 版覆盖本地版? [Y/n] " -r REPLY
        REPLY=${REPLY:-Y}
        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}安装已取消${NC}"
            exit 0
        fi
        echo -e "${GREEN}✓ 将用 Docker 版覆盖本地版${NC}"
    fi
else
    echo -e "${GREEN}✓ 未检测到已有安装${NC}"
fi

# 创建 wrapper 脚本
echo -e "${BLUE}[6/6]${NC} 安装 bootcs 命令..."

WRAPPER_SCRIPT='#!/bin/bash
# bootcs-cli Docker wrapper
# 自动生成，请勿手动编辑

IMAGE="ghcr.io/bootcs-dev/bootcs-cli:latest"
CONFIG_DIR="${HOME}/.bootcs"

# 确保配置目录存在
mkdir -p "${CONFIG_DIR}"

# 每日自动检查更新（后台静默执行，不阻塞用户）
check_update() {
    LAST_CHECK="${CONFIG_DIR}/.last_update_check"
    TODAY=$(date +%Y-%m-%d)
    
    if [ ! -f "$LAST_CHECK" ] || [ "$(cat "$LAST_CHECK" 2>/dev/null)" != "$TODAY" ]; then
        # 后台静默拉取最新镜像
        (docker pull "${IMAGE}" --quiet >/dev/null 2>&1; echo "$TODAY" > "$LAST_CHECK") &
    fi
}

# 手动更新命令
if [[ "$1" == "update" ]]; then
    echo "Checking for updates..."
    if docker pull "${IMAGE}"; then
        echo "✓ bootcs-cli is up to date"
        date +%Y-%m-%d > "${CONFIG_DIR}/.last_update_check"
    else
        echo "✗ Update failed"
        exit 1
    fi
    exit 0
fi

# 检查更新（后台执行）
check_update

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
echo -e "  ${YELLOW}4. 手动更新:${NC}"
echo -e "     ${BLUE}bootcs update${NC}"
echo ""
echo -e "  ${YELLOW}5. 查看帮助:${NC}"
echo -e "     ${BLUE}bootcs --help${NC}"
echo ""
echo -e "${YELLOW}提示: bootcs 会每天自动检查更新，无需手动操作${NC}"
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
