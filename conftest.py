import os
import sys

import allure
import pytest
from playwright.sync_api import Page

# 导入通用 fixtures 和钩子（browser_context、截图、Allure 报告生成等）
from core.conftest_base import (  # noqa: F401
    browser_context,
    env_name,
    pytest_addoption,
    pytest_configure,
    pytest_runtest_makereport,
    pytest_sessionfinish,
    settings,
)
from pages.login_page import LoginPage
from core.logger import logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def page(browser_context, settings):
    """会话登录。页面在整个测试会话内共享。"""
    logger.info(f"Creating New Page for env={settings.env}...")
    page = browser_context.new_page()
    login_page = LoginPage(page)
    # 导航到首页
    login_page.navigate_to_homepage()

    with allure.step("登录操作"):
        login_page.login(settings.get_system("main").username, settings.get_system("main").password)

    # with allure.step("验证登录是否成功"):
    #     page.wait_for_timeout(3000)
    #     assert login_page.is_login_successful(settings.get_system("main").expected_username), (
    #         "登录失败，未找到预期的用户名{}"
    #     )

    yield page
    page.close()
    logger.info("Page Closed.")
