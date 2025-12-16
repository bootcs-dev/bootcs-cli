# Contributing to bootcs-cli

感谢你对 bootcs-cli 的贡献兴趣！本文档面向开发者和贡献者。

## 项目背景

bootcs-cli 基于 [check50](https://github.com/cs50/check50) 和 [lib50](https://github.com/cs50/lib50) 扩展开发，用于 BootCS 平台的代码检查和提交。

> **注意**: 本项目与 CS50 课程本身没有直接关系，仅复用了 check50/lib50 的开源代码。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/bootcs-dev/bootcs-cli.git
cd bootcs-cli

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 运行测试

```bash
# 运行单元测试
pytest tests/unit/ -v

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=bootcs
```

## 代码风格

```bash
# 格式化代码
black bootcs/

# 代码检查
ruff check bootcs/
```

## 项目结构

```
bootcs-cli/
├── bootcs/
│   ├── __init__.py       # 版本信息
│   ├── __main__.py       # CLI 入口
│   ├── auth/             # 认证模块
│   │   ├── credentials.py    # 凭证存储
│   │   └── device_flow.py    # GitHub Device Flow
│   ├── api/              # API 客户端
│   │   ├── client.py         # HTTP 客户端
│   │   ├── submit.py         # 提交 API
│   │   └── checks.py         # 远程 checks 管理
│   ├── check/            # 检查模块 (基于 check50)
│   │   ├── _api.py           # 检查 API
│   │   ├── runner.py         # 检查运行器
│   │   └── c.py              # C 语言支持
│   └── lib50/            # 工具库 (基于 lib50)
│       ├── config.py         # YAML 配置加载
│       └── ...
├── docker/
│   └── Dockerfile        # 学员镜像
├── scripts/
│   ├── install-docker.sh     # Docker 版安装脚本
│   └── bootcs-wrapper.sh     # Docker wrapper
├── tests/
│   ├── unit/             # 单元测试
│   └── checks/           # 测试用 checks
├── pyproject.toml
├── DESIGN.md             # 设计文档
└── ROADMAP.md            # 路线图
```

## 环境变量

| 变量                 | 说明                          | 默认值                                |
| -------------------- | ----------------------------- | ------------------------------------- |
| `BOOTCS_API_URL`     | API 服务地址                  | `https://api.bootcs.dev`              |
| `BOOTCS_CHECKS_PATH` | 本地 checks 路径 (评测环境用) | -                                     |
| `BOOTCS_CLI_IMAGE`   | Docker 镜像 (开发用)          | `ghcr.io/bootcs-dev/bootcs-cli:latest` |

## Docker 镜像构建

```bash
# 本地构建
cd docker
docker build -t bootcs-cli:local .

# 测试本地镜像
BOOTCS_CLI_IMAGE=bootcs-cli:local ./scripts/bootcs-wrapper.sh --version
```

## 发布流程

1. 更新 `pyproject.toml` 中的版本号
2. 提交并推送到 main 分支
3. GitHub Actions 自动构建并推送 Docker 镜像

## 许可证

本项目基于 GPL-3.0 许可证发布，遵循 check50/lib50 的许可证要求。

## 致谢

本项目基于以下开源项目：

- [check50](https://github.com/cs50/check50) - CS50 代码检查工具
- [lib50](https://github.com/cs50/lib50) - CS50 工具库

感谢 CS50 团队的开源贡献！
