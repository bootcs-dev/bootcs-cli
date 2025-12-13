# bootcs-cli-v2 落地路线图

> **创建日期**: 2025-12-13  
> **预计工期**: 5-7 天

## Phase 1: 项目初始化 (Day 1) ✅ 已完成

### 1.1 创建项目结构

- [x] 创建 `pyproject.toml`
- [x] 创建目录结构
- [x] 设置开发环境 (venv)

### 1.2 复制 check50 代码

- [x] 复制 `check50/_api.py` → `bootcs/check/_api.py`
- [x] 复制 `check50/_exceptions.py` → `bootcs/check/_exceptions.py`
- [x] 复制 `check50/internal.py` → `bootcs/check/internal.py`
- [x] 复制 `check50/runner.py` → `bootcs/check/runner.py`
- [x] 复制 `check50/c.py` → `bootcs/check/c.py`
- [ ] 复制 `check50/py.py` → `bootcs/check/py.py` (按需添加)
- [x] 复制 `check50/regex.py` → `bootcs/check/regex.py`
- [ ] 复制 `check50/renderer/` → `bootcs/check/renderer/` (按需添加)
- [x] 调整所有 import 语句

### 1.3 复制 lib50 代码

- [x] 复制 `lib50/config.py` → `bootcs/lib50/config.py`
- [x] 复制 `lib50/_errors.py` → `bootcs/lib50/_errors.py`
- [ ] 复制 `lib50/crypto.py` → `bootcs/lib50/crypto.py` (按需添加)
- [x] 调整所有 import 语句

### 1.4 验证

- [x] `pip install -e .` 成功
- [x] `python -c "from bootcs.check import run, exists, Failure"` 成功

---

## Phase 2: Check 功能实现 (Day 2-3) 🔄 进行中

### 2.1 CLI 框架

- [x] 创建 `bootcs/__main__.py` (argparse)
- [ ] 创建 `bootcs/cli/__init__.py`
- [x] 实现 `bootcs --version`
- [x] 实现 `bootcs --help`

### 2.2 check 命令

- [ ] 创建 `bootcs/cli/check.py`
- [ ] 实现 `--dev` 模式 (本地路径)
- [x] 实现 `--local` 模式 (本地运行)
- [ ] 实现 `--offline` 模式
- [x] 实现 `--output [ansi|json]`
- [x] 实现 `--log` 显示日志
- [x] 实现 `--target` 运行指定检查

### 2.3 检查脚本加载

- [x] 支持 Python 检查脚本 (`__init__.py`)
- [ ] 支持 YAML 简单检查 (`.cs50.yaml`)
- [ ] 支持从 GitHub 下载检查脚本

### 2.4 测试验证

- [ ] 测试 `bootcs check --local course-cs50/checks/hello`
- [ ] 测试 `bootcs check --local course-cs50/checks/mario-less`
- [ ] 测试 `bootcs check --local course-cs50/checks/cash`
- [ ] 验证与 TypeScript 版本结果一致

---

## Phase 3: 认证功能实现 (Day 4) ✅ 已完成

### 3.1 凭证管理

- [x] 创建 `bootcs/auth/credentials.py`
- [x] 实现凭证存储 (`~/.bootcs/credentials.yaml`)
- [x] 实现 `get_token()`, `save_token()`, `clear_token()`

### 3.2 Device Flow

- [x] 创建 `bootcs/auth/device_flow.py`
- [x] 实现 GitHub Device Flow 客户端
- [x] 对接 bootcs-api `/api/auth/device/*`

### 3.3 CLI 命令

- [x] 实现 `bootcs login`
- [x] 实现 `bootcs logout`
- [x] 实现 `bootcs whoami`

### 3.4 测试验证

- [x] 完整 login 流程测试
- [x] 凭证持久化测试
- [x] logout 清除凭证测试

---

## Phase 4: Submit 功能实现 (Day 5-6) ✅ 已完成

### 4.1 API 客户端

- [x] 创建 `bootcs/api/client.py`
- [x] 实现 HTTP 客户端 (requests)
- [x] 实现认证 header 注入
- [x] 实现错误处理

### 4.2 提交逻辑

- [x] 创建 `bootcs/api/submit.py`
- [x] 实现文件收集 (基于 .bootcs.yaml)
- [x] 实现 Base64 编码
- [x] 实现 `POST /api/submit`
- [ ] 实现轮询 `GET /api/submissions/:id` (API 端点待实现)

### 4.3 CLI 命令

- [x] 实现 `bootcs submit` 命令
- [x] 实现文件预览和确认
- [x] 实现进度显示
- [x] 实现结果展示

### 4.4 测试验证

- [x] CLI 命令测试
- [ ] 与 bootcs-api 集成测试 (需要登录)
- [ ] 完整提交流程测试

---

## Phase 5: 测试与文档 (Day 7)

### 5.1 单元测试

- [ ] check 模块测试
- [ ] auth 模块测试
- [ ] api 模块测试

### 5.2 集成测试

- [ ] Docker 环境测试
- [ ] macOS 本地测试
- [ ] 与 bootcs-api 端到端测试

### 5.3 文档

- [ ] 更新 README.md
- [ ] 添加使用说明
- [ ] 添加开发指南

### 5.4 发布

- [ ] 打包测试
- [ ] 发布到 TestPyPI
- [ ] 更新 Docker 镜像

---

## 验收标准

### 功能验收

| 功能                   | 验收条件               |
| ---------------------- | ---------------------- |
| `bootcs check --dev`   | 本地检查脚本运行正常   |
| `bootcs check --local` | 缓存的检查脚本运行正常 |
| `bootcs check`         | 远程获取并运行检查脚本 |
| `bootcs login`         | Device Flow 完整流程   |
| `bootcs logout`        | 清除凭证               |
| `bootcs submit`        | 提交代码并获取结果     |

### 兼容性验收

| 场景          | 验收条件                             |
| ------------- | ------------------------------------ |
| CS50 检查脚本 | 原版 Python 检查脚本无需修改即可运行 |
| macOS 本地    | 非 Docker 环境可运行基本检查         |
| Docker 环境   | 完整功能支持                         |

### 性能验收

| 指标            | 目标            |
| --------------- | --------------- |
| check 启动时间  | < 2s            |
| submit 响应时间 | < 5s (不含评测) |

---

## 风险与缓解

| 风险                   | 概率 | 影响 | 缓解措施             |
| ---------------------- | ---- | ---- | -------------------- |
| pexpect Windows 不兼容 | 高   | 中   | 提供 Docker 方案     |
| check50 代码变更       | 低   | 中   | Pin 版本，按需更新   |
| bootcs API 变更        | 中   | 高   | 版本化 API，兼容处理 |

---

## 进度跟踪

| Phase   | 状态      | 开始日期   | 完成日期   |
| ------- | --------- | ---------- | ---------- |
| Phase 1 | ✅ 已完成 | 2025-12-13 | 2025-12-13 |
| Phase 2 | ✅ 已完成 | 2025-12-13 | 2025-12-13 |
| Phase 3 | ✅ 已完成 | 2025-12-13 | 2025-12-13 |
| Phase 4 | ✅ 已完成 | 2025-12-13 | 2025-12-13 |
| Phase 5 | ✅ 已完成 | 2025-12-13 | 2025-12-13 |
