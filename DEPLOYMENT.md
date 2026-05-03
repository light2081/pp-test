# pp-test 框架部署和使用说明

## 概述

pp-test 是一个基于 Playwright + pytest 的 Web UI 自动化测试框架，使用 Allure 生成测试报告。本文档提供了框架的部署、配置和使用说明。

## 环境要求

### 系统要求
- Python 3.8 或更高版本
- 操作系统：Windows、macOS 或 Linux

### 依赖软件
- Chrome 浏览器（Playwright 会自动安装对应版本的浏览器）
- Node.js（Playwright 需要 Node.js 运行时）
- Allure 命令行工具（用于生成和查看测试报告）

## 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd pp-test
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 安装 Allure 命令行工具
```bash
# Linux/macOS
wget https://github.com/allure-framework/allure2/releases/download/2.20.1/allure-2.20.1.zip
unzip allure-2.20.1.zip
sudo mv allure-2.20.1 /usr/local/bin/allure

# Windows
# 1. 下载 Allure 命令行工具：https://github.com/allure-framework/allure2/releases
# 2. 解压到指定目录
# 3. 将 bin 目录添加到系统 PATH 环境变量
```

### 4. 安装 Playwright 浏览器
```bash
playwright install
```

## 配置说明

### 环境配置文件

框架支持多环境配置，配置文件位于 `config/` 目录：

- `base.ini`: 基础配置（所有环境共享）
- `dev.ini`: DEV 环境配置
- `test.ini`: TEST 环境配置

### 配置项说明

#### 基础配置 (`base.ini`)
```ini
[system]
url = http://example.com  # 测试网站 URL
username = testuser       # 默认用户名
password = testpass       # 默认密码

[runtime]
browser = chromium        # 浏览器类型（chromium, firefox, webkit）
headless = false         # 是否以无头模式运行
timeout = 30000          # 超时时间（毫秒）
screenshot_on_failure = true  # 失败时截图

[paths]
log_dir = logs           # 日志目录
screenshot_dir = screenshots  # 截图目录
report_dir = report      # 报告目录
upload_file = testdata/dev/upload_file.txt  # 上传文件路径
```

#### 环境特定配置
每个环境配置文件可以覆盖基础配置中的特定值。

## 使用方法

### 1. 编写测试用例

测试文件位于 `testcase/` 目录，遵循 pytest 命名规范：
- 文件名：`test_*.py`
- 类名：`Test*`
- 函数名：`test_*`

#### 示例测试用例
```python
import pytest
from pages.login_page import LoginPage
from core.settings import load_settings

class TestLogin:
    @pytest.mark.smoke
    def test_login_success(self, page):
        login_page = LoginPage(page)
        login_page.navigate_to_homepage()
        login_page.login(load_settings().get_system("system").username, load_settings().get_system("system").password)
        assert "Dashboard" in page.title()
```

### 2. 页面类开发

页面类位于 `pages/` 目录，继承自 `pages.base_page.BasePage`：

```python
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "button[type='submit']"

    def login(self, username, password):
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)
```

### 3. 使用页面操作回退机制

页面基类提供了带回退的选择器操作，支持多个选择器依次尝试：

```python
# 单个选择器
self.click("#login-button")

# 多个选择器（回退机制）
self.click_with_fallbacks("#login-button, button.login, input[type='submit']")
```

## 运行测试

### 基本命令

```bash
python main.py  # 运行 DEV 环境测试，默认标记为 regression
python main.py --env=TEST  # 运行 TEST 环境测试
```

### 运行特定测试

```bash
python main.py --env=DEV -k "test_login"  # 运行包含 "test_login" 的测试
python main.py --env=DEV -m "smoke"      # 运行标记为 smoke 的测试
```

### 运行单个测试用例

可以直接使用 pytest 运行单个测试用例，提供更精确的控制：

```bash
# 运行指定文件中的所有测试
pytest testcase/test_010_add_cart.py --env=DEV

# 运行指定文件中的特定测试类
pytest testcase/test_010_add_cart.py::TestAddCart --env=DEV

# 运行指定文件中的特定测试方法
pytest testcase/test_010_add_cart.py::TestAddCart::test_add_item_to_cart --env=DEV

# 运行包含特定字符串的测试
pytest -k "add_cart" --env=DEV

# 运行标记为 smoke 的测试
pytest -m smoke --env=DEV

# 使用相对路径运行测试（推荐）
pytest ./testcase/test_010_add_cart.py --env=DEV

# 使用绝对路径运行测试
pytest /path/to/your/project/testcase/test_010_add_cart.py --env=DEV
```

### pytest 参数支持

框架支持所有 pytest 参数：

```bash
python main.py --env=DEV -v           # 详细输出
python main.py --env=DEV -x           # 遇到失败立即停止
python main.py --env=DEV --tb=short   # 简短回溯信息
pytest --env=DEV -q                  # 简洁输出
pytest --env=DEV --collect-only      # 仅收集测试，不执行
pytest --env=DEV --lf               # 运行上次失败的测试
pytest --env=DEV --tb=long          # 详细回溯信息
```

## 生成和查看报告

### 生成 Allure 报告

测试运行后会自动生成 Allure 报告，报告路径为：
```
report/reportYYYYMMDDHHmm/index.html
```

### 使用报告服务器查看报告

使用 `report_server.py` 启动报告服务器，然后在浏览器中访问：

```bash
python report_server.py
```

服务器将在 `http://localhost:8100` 启动，您可以在浏览器中访问该地址查看 Allure 报告。

## 调试技巧

### 生成详细日志

运行测试时日志文件会保存在运行目录的 `logs` 子目录。

### 截图和页面信息

失败时自动截取屏幕并收集页面信息（链接、输入框、按钮等）。

### 调试模式

使用 `--debug` 标志运行测试以获取更多调试信息：
```bash
python main.py --env=DEV --debug
```

## 常见问题

### Q: 测试运行失败，如何获取更多信息？
A: 检查 `logs` 目录中的日志文件，查看详细的错误信息。

### Q: 如何处理文件上传？
A: 框架提供了文件上传对话框处理功能，确保上传文件路径正确配置。

### Q: 如何处理弹窗或新页面？
A: 使用 `click_link_and_switch_to_new_page()` 方法处理链接点击和新页面切换。

### Q: 如何自定义测试数据？
A: 使用 `initialize_test_data()` 方法加载和初始化测试数据。

## 高级功能

### 环境隔离
每个测试运行创建独立的运行目录，确保测试环境隔离。

### Allure 报告集成
所有操作自动记录到 Allure 报告，包含步骤、日志和截图。

### 页面操作回退机制
页面基类提供带回退的选择器操作，支持多个选择器依次尝试。

## 贡献指南

1. 遵循项目的编码规范
2. 编写测试用例覆盖新功能
3. 更新相关文档
4. 提交 Pull Request

## 联系信息

如有问题或建议，请提交 Issue 或联系维护团队。