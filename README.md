# bootcs-cli

**BootCS 代码检查工具** - 在本地验证你的代码是否正确，然后提交到平台评测。

✨ **支持多语言**: C, Java, Python, SQL - 同一个问题，自由选择你喜欢的语言！

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

### 自动检测语言

bootcs-cli 会**自动识别**你使用的编程语言：

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

### 多语言支持

**同一个问题可以用不同语言完成！** 系统根据目录中的源文件自动判断：

| 语言   | 文件名示例     | 自动检测 |
| ------ | -------------- | -------- |
| C      | `hello.c`      | ✅       |
| Java   | `Hello.java`   | ✅       |
| Python | `hello.py`     | ✅       |
| SQL    | `1.sql, 2.sql` | ✅       |

**示例 - 用 Python 完成 hello 问题**：

```bash
# hello.py
name = input("What's your name? ")
print(name)
```

```bash
bootcs check cs50/hello
# 自动识别为 Python，无需 -L 参数
```

**示例 - 用 Java 完成 hello 问题**：

```java
// Hello.java
import java.util.Scanner;

public class Hello {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("What's your name? ");
        String name = scanner.nextLine();
        System.out.println(name);
    }
}
```

```bash
bootcs check cs50/hello
# 自动识别为 Java
```

### 常用选项

```bash
# 手动指定语言（通常不需要）
bootcs check cs50/hello -L python
bootcs check cs50/hello -L java
bootcs check cs50/hello -L c

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

系统会显示要提交的文件列表，确认后上传，并**自动等待评测结果**：

```
📦 Submitting cs50/hello

Files to submit:
  • hello.c

Submit these files? [Y/n] Y
Submitting...

✅ Submitted successfully!
   Submission ID: cmj9tcg3p00kfi7z4ih3l6quz
   Short Hash:    f3b2fac3

⏳ Evaluating... ⠹ (3s)

🎉 Evaluation Complete!

   Status:  SUCCESS
   Passed:  4/4

   ✅ file_exists
   ✅ compiles
   ✅ emma
   ✅ rodrigo
```

### 提交选项

```bash
# 跳过确认，直接提交
bootcs submit cs50/hello -y

# 异步模式：提交后立即返回，不等待结果
bootcs submit cs50/hello --async

# 自定义超时时间（默认 60 秒）
bootcs submit cs50/hello --timeout 120
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

### 语言检测相关

**Q: 如何选择编程语言？**

A: 创建对应语言的源文件即可：

- C: `hello.c`
- Java: `Hello.java` (注意首字母大写，与类名一致)
- Python: `hello.py`

系统会自动检测。混合多个语言文件时，按数量多的为准。

**Q: 能否手动指定语言？**

A: 可以使用 `-L` 参数：`bootcs check cs50/hello -L python`

**Q: Java 文件名必须大写吗？**

A: 是的。Java 遵循 PascalCase 命名约定（如 `Hello.java`, `MarioLess.java`），这是 Java 语言的标准规范。

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

### 架构说明

**统一语言适配器架构** (v2.0+):

- ✅ 单一 check 定义支持多语言（C/Java/Python）
- ✅ 自动语言检测和命名规则转换
- ✅ 编译语言与解释语言差异化处理
- ✅ 工厂模式 + 适配器模式实现
- ✅ 145+ 单元测试，100% 覆盖率

详见 `docs/LANGUAGE-ADAPTER-DESIGN.md`

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
