#!/bin/bash
# BootCS CLI 安装脚本
# 用法: curl -fsSL https://bootcs.cn/install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Installing BootCS CLI...${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# 确定安装目录
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

# 创建 bootcs 脚本
BOOTCS_SCRIPT="$INSTALL_DIR/bootcs"

cat > "$BOOTCS_SCRIPT" << 'EOF'
#!/bin/bash
# BootCS CLI Wrapper
# https://bootcs.cn

# 默认使用 cs50 镜像，可通过环境变量覆盖
BOOTCS_IMAGE="${BOOTCS_IMAGE:-ghcr.io/bootcs-cn/bootcs-cli:cs50}"

# 运行容器
docker run --rm -v "$(pwd)":/workspace "$BOOTCS_IMAGE" "$@"
EOF

chmod +x "$BOOTCS_SCRIPT"

# 检查 PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Please add $INSTALL_DIR to your PATH:${NC}"
    echo ""
    
    # 检测 shell 类型
    SHELL_NAME=$(basename "$SHELL")
    if [[ "$SHELL_NAME" == "zsh" ]]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
        echo "   source ~/.zshrc"
    elif [[ "$SHELL_NAME" == "bash" ]]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "   source ~/.bashrc"
    else
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
    echo ""
fi

echo -e "${GREEN}✅ BootCS CLI installed successfully!${NC}"
echo ""
echo "Usage:"
echo "   bootcs check cs50/credit    # 检查作业"
echo "   bootcs --help               # 查看帮助"
echo ""
echo "To use a different course image:"
echo "   BOOTCS_IMAGE=ghcr.io/bootcs-cn/bootcs-cli:other bootcs check ..."
