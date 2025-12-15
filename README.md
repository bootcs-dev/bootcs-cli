# bootcs-cli

BootCS 命令行工具 - 用于代码检查和提交

基于 [check50](https://github.com/cs50/check50) 和 [lib50](https://github.com/cs50/lib50) 扩展开发，用于 BootCS 平台的代码检查和提交。

> **注意**: 本项目与 CS50 课程本身没有直接关系，仅复用了 check50/lib50 的开源代码。

## 功能

- ✅ **代码检查** - 本地运行检查脚本验证代码正确性
- ✅ **GitHub 登录** - 使用 Device Flow 进行 GitHub 认证
- ✅ **代码提交** - 将代码提交到 BootCS 平台进行评测
- ✅ **远程 Checks** - 自动从服务器下载检查脚本
- ✅ **多语言支持** - 自动检测 C、Python 等编程语言
- ✅ **缓存管理** - 本地缓存检查脚本，提高效率

## 安装

### 🐳 推荐方式：Docker 版（无需配置环境）

Docker 版开箱即用，包含 C/Python/Java 完整开发环境，与评测环境完全一致。

**一键安装：**

```bash
curl -fsSL https://raw.githubusercontent.com/bootcs-cn/bootcs-cli/main/scripts/install-docker.sh | bash
```

**手动安装：**

```bash
# 1. 拉取镜像
docker pull ghcr.io/bootcs-cn/bootcs-cli:latest

# 2. 下载 wrapper 脚本
sudo curl -fsSL -o /usr/local/bin/bootcs \
  https://raw.githubusercontent.com/bootcs-cn/bootcs-cli/main/scripts/bootcs-wrapper.sh
sudo chmod +x /usr/local/bin/bootcs
```

安装后，使用方式与本地安装完全一致：

```bash
bootcs login              # 登录（仅需一次）
bootcs check cs50/hello   # 检查代码
bootcs submit cs50/hello  # 提交代码
```

> 💡 **提示**: Docker 版会自动持久化凭证到 `~/.bootcs/`，登录一次即可长期使用。

### 本地安装：pip

如果你更喜欢本地安装（需要自行配置 C/Python 环境）：

```bash
pip install git+https://github.com/bootcs-cn/bootcs-cli.git
```

### 开发模式安装

```bash
git clone https://github.com/bootcs-cn/bootcs-cli.git
cd bootcs-cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 快速开始

### 1. 登录

\`\`\`bash
bootcs login
\`\`\`

按照提示访问 GitHub 并输入验证码完成登录。

### 2. 检查代码

\`\`\`bash

# 进入你的代码目录

cd ~/projects/hello

# 检查代码（自动下载 checks，自动检测语言）

bootcs check cs50/hello

# 指定语言

bootcs check cs50/hello -L python

# 强制更新 checks

bootcs check cs50/hello -u

# 输出 JSON 格式

bootcs check cs50/hello --output json
\`\`\`

### 3. 提交代码

\`\`\`bash

# 提交代码到 BootCS 平台

bootcs submit cs50/hello

# 跳过确认

bootcs submit cs50/hello -y

# 自定义提交消息

bootcs submit cs50/hello -m "Fix bug"
\`\`\`

### 4. 管理缓存

\`\`\`bash

# 查看已缓存的 checks

bootcs cache list

# 清空所有缓存

bootcs cache clear

# 清空特定课程的缓存

bootcs cache clear cs50
\`\`\`

### 5. 账户管理

\`\`\`bash

# 查看当前登录用户

bootcs whoami

# 登出

bootcs logout
\`\`\`

## 命令参考

| 命令                      | 说明             |
| ------------------------- | ---------------- |
| \`bootcs --version\`      | 显示版本号       |
| \`bootcs --help\`         | 显示帮助信息     |
| \`bootcs login\`          | 使用 GitHub 登录 |
| \`bootcs logout\`         | 登出             |
| \`bootcs whoami\`         | 显示当前登录用户 |
| \`bootcs check <slug>\`   | 检查代码         |
| \`bootcs submit <slug>\`  | 提交代码         |
| \`bootcs cache <action>\` | 管理缓存         |

### check 命令选项

| 选项                    | 说明                        |
| ----------------------- | --------------------------- | --------------------- |
| \`-L, --language LANG\` | 指定语言 (自动检测如不指定) |
| \`-u, --update\`        | 强制更新 checks             |
| \`--output [ansi        | json]\`                     | 输出格式 (默认: ansi) |
| \`--log\`               | 显示详细日志                |
| \`--target NAME\`       | 只运行指定的检查            |
| \`--local PATH\`        | 使用本地检查脚本目录        |

### submit 命令选项

| 选项                  | 说明                |
| --------------------- | ------------------- |
| \`-L, --language\`    | 指定语言 (自动检测) |
| \`-m, --message MSG\` | 自定义提交消息      |
| \`-y, --yes\`         | 跳过确认提示        |
| \`--local PATH\`      | 使用本地配置目录    |

### cache 命令选项

| 选项               | 说明                    |
| ------------------ | ----------------------- |
| \`list\`           | 列出所有缓存的 checks   |
| \`clear [slug]\`   | 清空缓存 (可选指定课程) |
| \`-L, --language\` | 指定语言                |

## 语言自动检测

CLI 会根据当前目录的文件自动检测编程语言：

| 文件扩展名        | 检测为     |
| ----------------- | ---------- |
| \`.c\`, \`.h\`    | C          |
| \`.py\`           | Python     |
| \`.js\`, \`.mjs\` | JavaScript |
| \`.go\`           | Go         |
| \`.rs\`           | Rust       |

如果目录有多种语言的文件，会选择文件数量最多的语言。

## 开发

\`\`\`bash

# 安装开发依赖

pip install -e ".[dev]"

# 运行单元测试

pytest tests/unit/ -v

# 运行所有测试

pytest

# 代码格式化

black bootcs/
ruff check bootcs/
\`\`\`

## 项目结构

\`\`\`
bootcs-cli/
├── bootcs/
│ ├── **init**.py # 版本信息
│ ├── **main**.py # CLI 入口
│ ├── auth/ # 认证模块
│ │ ├── credentials.py
│ │ └── device_flow.py
│ ├── api/ # API 客户端
│ │ ├── client.py
│ │ ├── submit.py
│ │ └── checks.py # 远程 checks 管理
│ ├── check/ # 检查模块 (基于 check50)
│ │ ├── \_api.py
│ │ ├── runner.py
│ │ └── c.py
│ └── lib50/ # 工具库 (基于 lib50)
│ ├── config.py
│ └── ...
├── tests/
│ └── unit/ # 单元测试
├── pyproject.toml
└── README.md
\`\`\`

## 环境变量

| 变量                   | 说明                          | 默认值                    |
| ---------------------- | ----------------------------- | ------------------------- |
| \`BOOTCS_API_URL\`     | API 服务地址                  | \`https://api.bootcs.cn\` |
| \`BOOTCS_CHECKS_PATH\` | 本地 checks 路径 (评测环境用) | -                         |

## 许可证

本项目基于 GPL-3.0 许可证发布，遵循 check50/lib50 的许可证要求。

## 致谢

本项目基于以下开源项目：

- [check50](https://github.com/cs50/check50) - CS50 代码检查工具
- [lib50](https://github.com/cs50/lib50) - CS50 工具库

感谢 CS50 团队的开源贡献！
