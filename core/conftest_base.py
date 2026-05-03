"""
通用 pytest fixtures 和钩子，项目层 conftest.py 导入此模块后即可获得：
  - browser_context：会话级浏览器上下文
  - pytest_runtest_makereport：用例失败时自动截图
  - pytest_sessionfinish：写入 Allure environment.properties / executor.json

项目层 conftest.py 只需再实现 page fixture 完成项目特有的登录逻辑。

用法：
    # your_project/conftest.py
    from core.conftest_base import *   # noqa: F401,F403
    import pytest
    from pages.login_page import LoginPage

    @pytest.fixture(scope="session")
    def page(browser_context, settings):
        page = browser_context.new_page()
        LoginPage(page).login(settings.get_system("main").url, ...)
        yield page
        page.close()
"""

import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

import allure
import pytest
from playwright.sync_api import sync_playwright

from core.logger import configure_logger, logger
from core.settings import (
    ensure_runtime_dirs,
    load_settings,
    resolve_env_name,
    set_current_env,
)


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=os.getenv("TEST_ENV", "DEV"),
        choices=["DEV", "TEST"],
        help="指定运行环境，默认 DEV",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    env_name = set_current_env(config.getoption("--env"))
    settings = ensure_runtime_dirs(load_settings(env_name))
    configure_logger(settings.paths.logs_dir)

    if not getattr(config.option, "allure_report_dir", None):
        config.option.allure_report_dir = str(settings.paths.allure_results_dir)
    if not getattr(config.option, "clean_alluredir", False):
        config.option.clean_alluredir = True
    if not getattr(config.option, "log_file", None):
        config.option.log_file = str(settings.paths.logs_dir / "pytest.log")


@pytest.fixture(scope="session")
def env_name():
    return resolve_env_name()


@pytest.fixture(scope="session")
def settings(env_name):
    return ensure_runtime_dirs(load_settings(env_name))


@pytest.fixture(scope="session")
def browser_context(settings):
    """初始化浏览器上下文（会话级，所有测试共享）。"""
    logger.info(f"Initializing Browser Context for env={settings.env}...")
    with sync_playwright() as playwright:
        browser_launcher = getattr(playwright, settings.runtime.browser)
        browser = browser_launcher.launch(
            headless=settings.runtime.headless,
            args=["--start-maximized"],
        )
        context = browser.new_context(no_viewport=True)
        yield context
        context.close()
        browser.close()
        logger.info("Browser Context Closed.")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动截图并附加到 Allure 报告。"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        logger.error(f"Test Failed: {item.name}")
        page = item.funcargs.get("page")
        if page:
            try:
                settings = load_settings()
                settings.paths.screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = "".join(
                    c for c in item.name if c.isalnum() or c in ("_", "-")
                )
                screenshot_path = (
                    settings.paths.screenshots_dir / f"fail_{safe_name}_{timestamp}.png"
                )
                page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved to {screenshot_path}")
                with open(screenshot_path, "rb") as f:
                    allure.attach(
                        f.read(),
                        name=f"Failure_{safe_name}_{timestamp}",
                        attachment_type=allure.attachment_type.PNG,
                    )
            except Exception as exc:
                logger.error(f"Failed to take screenshot: {exc}")


def pytest_sessionfinish(session, exitstatus):
    """生成 Allure environment.properties 和 executor.json。"""
    settings = ensure_runtime_dirs(load_settings())
    report_dir = Path(
        session.config.getoption("--alluredir") or settings.paths.allure_results_dir
    )
    report_dir.mkdir(parents=True, exist_ok=True)

    env_file = report_dir / "environment.properties"
    try:
        lines = [
            f"Environment={settings.env}",
            f"Python.Version={sys.version.split()[0]}",
            f"Platform={platform.system()} {platform.release()}",
            f"Browser={settings.runtime.browser}",
        ]
        for name, sys_cfg in settings.systems.items():
            lines.append(f"System.{name}.URL={sys_cfg.url}")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        logger.info(f"Generated environment.properties at {env_file}")
    except Exception as exc:
        logger.error(f"Failed to generate environment.properties: {exc}")

    executor_file = report_dir / "executor.json"
    try:
        executor_info = {
            "name": "Local Execution",
            "type": "local",
            "reportName": f"{settings.env} Test Report",
            "buildName": f"{settings.env} Local Run",
        }
        with open(executor_file, "w", encoding="utf-8") as f:
            json.dump(executor_info, f, indent=4, ensure_ascii=False)
        logger.info(f"Generated executor.json at {executor_file}")
    except Exception as exc:
        logger.error(f"Failed to generate executor.json: {exc}")
