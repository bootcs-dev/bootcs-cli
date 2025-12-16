# bootcs-cli

**BootCS 代码检查工具** - 在本地验证你的代码是否正确，然后提交到平台评测。

## 🚀 30 秒上手

```bash
# 1. 安装（只需一次）
curl -fsSL https://raw.githubusercontent.com/bootcs-dev/bootcs-cli/main/scripts/install-docker.sh | bash

# 2. 登录（只需一次）
bootcs login

# 3. 写代码，然后检查
cd ~/my-code/hello
bootcs check cs50/hello

# 4. 全部通过后，提交
bootcs submit cs50/hello
```

## 📦 安装

### 推荐方式：一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/bootcs-dev/bootcs-cli/main/scripts/install-docker.sh | bash
```

> 需要先安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 验证安装

```bash
bootcs --version
# 输出: bootcs 2.0.0
```

## 🔐 登录

首次使用需要登录 GitHub：

```bash
bootcs login
```

按提示操作：

1. 访问显示的链接
2. 输入验证码
3. 授权 BootCS

登录成功后，凭证会保存在本地，无需重复登录。

## ✅ 检查代码

进入你的代码目录，运行检查：

```bash
cd ~/projects/hello
bootcs check cs50/hello
```

示例输出：

```
🔍 Running checks for cs50/hello...

✅ hello.c exists
✅ hello.c compiles
✅ responds to name Emma
✅ responds to name Rodrigo

🎉 Results: 4 passed
```

### 常用选项

```bash
# Python 作业（自动检测语言，通常不需要指定）
bootcs check cs50/hello -L python

# 强制重新下载检查脚本
bootcs check cs50/hello -u

# 查看详细日志
bootcs check cs50/hello --log
```

## 📤 提交代码

本地检查全部通过后，提交到平台：

```bash
bootcs submit cs50/hello
```

系统会显示要提交的文件列表，确认后上传。

```bash
# 跳过确认，直接提交
bootcs submit cs50/hello -y
```

## 📋 常用命令速查

| 命令                   | 说明         |
| ---------------------- | ------------ |
| `bootcs check <slug>`  | 检查代码     |
| `bootcs submit <slug>` | 提交代码     |
| `bootcs login`         | 登录         |
| `bootcs logout`        | 登出         |
| `bootcs whoami`        | 查看当前用户 |
| `bootcs --help`        | 查看帮助     |

## ❓ 常见问题

### Docker 未运行

```
Error: Docker is not running
```

**解决**: 启动 Docker Desktop 应用。

### 检查脚本未找到

```
Error: Could not find checks for 'xxx'
```

**解决**:

1. 确认 slug 拼写正确（如 `cs50/hello`）
2. 确认已登录：`bootcs login`

### 登录失败

**解决**:

1. 检查网络连接
2. 重试：`bootcs login`

## 📚 更多帮助

- [BootCS 官网](https://bootcs.dev)
- [课程文档](https://docs.bootcs.dev)

---

<details>
<summary>🔧 高级选项（开发者）</summary>

### 本地安装（不使用 Docker）

如果你不想使用 Docker，可以用 pip 安装：

```bash
pip install git+https://github.com/bootcs-dev/bootcs-cli.git
```

需要自行配置 C/Python/Java 编译环境。

### 环境变量

| 变量                 | 说明             | 默认值                   |
| -------------------- | ---------------- | ------------------------ |
| `BOOTCS_API_URL`     | API 地址         | `https://api.bootcs.dev` |
| `BOOTCS_CHECKS_PATH` | 本地 checks 路径 | -                        |

### 开发模式

```bash
git clone https://github.com/bootcs-dev/bootcs-cli.git
cd bootcs-cli
pip install -e ".[dev]"
pytest
```

</details>
