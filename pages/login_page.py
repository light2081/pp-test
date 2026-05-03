import allure

from pages.base_page import BasePage
from core.logger import logger


class LoginPage(BasePage):
    """登录页面对象类"""

    # 页面元素定位器
    USERNAME_INPUT = "textbox[name='Username']"
    PASSWORD_INPUT = "textbox[name='Password']"
    LOGIN_BUTTON = "button[name='Login']"

    def login(self, username: str, password: str) -> None:
        """
        执行登录操作

        :param username: 用户名
        :param password: 密码
        """
        logger.info(f"开始登录，用户: {username}")

        with allure.step(f"输入用户名: {username}"):
            input_username = self.page.get_by_role("textbox", name="Username")
            input_username.wait_for(state="visible", timeout=10000)
            input_username.fill(username)
            logger.debug(f"用户名输入完成: {username}")

        with allure.step("输入密码"):
            input_password = self.page.get_by_role("textbox", name="Password")
            input_password.wait_for(state="visible", timeout=10000)
            input_password.fill(password)
            logger.debug("密码输入完成")

        with allure.step("点击登录按钮"):
            btn_login = self.page.get_by_role("button", name="Login")
            btn_login.wait_for(state="visible", timeout=10000)
            btn_login.click()
            logger.debug("登录按钮点击完成")

        self.wait_for_page_load(3000)
        logger.info("登录操作完成")