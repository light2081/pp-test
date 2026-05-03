# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 Playwright + pytest 的 Web UI 自动化测试框架，使用 Allure 生成测试报告。框架支持多环境配置（DEV, TEST），包含验证码识别、页面操作回退机制等高级功能。

## 开发命令

### 运行测试
```bash
python main.py --env=DEV  # 运行 DEV 环境测试，默认标记为 regression
python main.py --env=TEST  # 运行 TEST 环境测试
python main.py --env=DEV -k "test_login"  # 运行特定测试
```

### 生成 Allure 报告
测试运行后会自动生成 Allure 报告，报告路径为 `report/reportYYYYMMDDHHmm/index.html`

### 环境配置
配置文件位于 `config/` 目录，包含：
- `base.ini`: 基础配置
- `dev.ini`: DEV 环境配置  
- `test.ini`: TEST 环境配置

## 代码架构

### 核心模块结构
```
core/
├── settings.py      # 配置管理（环境、系统、运行时、路径配置）
├── base_page.py     # 页面基类，提供通用操作和 Allure 集成
├── logger.py        # 日志配置
├── common.py        # 通用工具函数
└── data_loader.py   # 数据加载（YAML 等）
```

### 页面类结构
```
pages/
├── base_page.py     # 页面基类（继承自 core.base_page.BasePage）
└── login_page.py   # 具体页面实现
```

### 测试文件
测试文件位于 `testcase/` 目录，遵循 pytest 命名规范：
- 文件名：`test_*.py`
- 类名：`Test*`
- 函数名：`test_*`

### 配置系统
使用 `core.settings` 模块管理配置，支持：
- 多环境配置（DEV, TEST）
- 系统配置（URL、用户名、密码）
- 运行时配置（浏览器、headless 模式、超时）
- 路径配置（日志、截图、报告目录）

## 关键特性

### 1. 页面操作回退机制
页面基类提供带回退的选择器操作，如 `click_with_fallbacks()`，支持多个选择器依次尝试。

### 2. Allure 报告集成
所有操作自动记录到 Allure 报告，包含步骤、日志和截图。

### 3. 验证码识别
集成 ddddocr 库进行验证码识别，可通过 `recognize_captcha()` 方法使用。

### 4. Windows 文件对话框处理
针对 Windows 环境优化文件上传对话框的处理。

### 5. 环境隔离
每个测试运行创建独立的运行目录，确保测试环境隔离。

## 开发规范

### 页面类开发
1. 继承 `pages.base_page.BasePage`
2. 定义页面元素选择器
3. 实现页面特定操作方法
4. 使用 Allure 步骤装饰器

### 测试开发
1. 使用 pytest 标记（smoke, regression, critical, debug）
2. 遵循 Arrange-Act-Assert 模式
3. 利用页面类进行操作
4. 添加适当的断言和验证

## 调试技巧

### 生成详细日志
运行测试时日志文件会保存在运行目录的 logs 子目录。

### 截图和页面信息
失败时自动截取屏幕并收集页面信息（链接、输入框、按钮等）。

### 验证码处理
如需手动处理验证码，可在测试中覆盖 `recognize_captcha()` 方法。