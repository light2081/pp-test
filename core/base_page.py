import allure
import os
import random
import string
import sys
from pathlib import Path
from collections.abc import Callable

from playwright.sync_api import Page, expect  # noqa: F401

from core.data_loader import read_yaml
from core.logger import logger
from core.settings import load_settings

if sys.platform == "win32":
    import ctypes
    _user32 = ctypes.windll.user32
    _WM_SETTEXT = 0x000C
    _BM_CLICK = 0x00F5
else:
    _user32 = None
    _WM_SETTEXT = _BM_CLICK = None


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    @staticmethod
    def generate_random_uppercase(length: int = 8) -> str:
        return "".join(random.choice(string.ascii_uppercase) for _ in range(length))

    def load_test_data(self, file_name: str) -> dict:
        test_data = read_yaml(file_name)
        if not isinstance(test_data, dict):
            raise TypeError(
                f"{file_name} 的内容必须是字典，当前实际类型为 {type(test_data).__name__}"
            )
        return test_data

    def initialize_test_data(
        self,
        file_name: str,
        generated_fields: dict[str, Callable[[], object]] | None = None,
        reset_fields: dict[str, object] | None = None,
    ) -> dict:
        test_data = self.load_test_data(file_name)
        for field_name, value_factory in (generated_fields or {}).items():
            test_data[field_name] = value_factory()
        for field_name, value in (reset_fields or {}).items():
            test_data[field_name] = value
        return test_data

    def open(self, url):
        with allure.step(f"Navigate to {url}"):
            logger.info(f"Navigating to {url}")
            self.page.goto(url)

    def navigate_to_homepage(self):
        """导航到首页。"""
        self.open(load_settings().get_system("main").url) # type: ignore
        self.wait_for_page_load(3000)

    def close(self):
        with allure.step("Close current page"):
            logger.info("Closing current page")
            self.page.close()

    def get_upload_file_path(self) -> str:
        upload_file = load_settings().runtime.upload_file
        if not upload_file.exists():
            raise FileNotFoundError(f"上传文件不存在: {upload_file}")
        return str(upload_file)

    def click(self, selector: str):
        with allure.step(f"Click element: {selector}"):
            logger.info(f"Clicking element: {selector}")
            self.page.locator(selector).click()

    def click_with_fallbacks(self, selectors: str, index: int = 0, timeout: int = 3000):
        """依次尝试多个 selector，点击指定索引处的元素。"""
        selector_list = [s.strip() for s in selectors.split(",")]
        with allure.step(f"Try clicking elements: {selectors} (index: {index})"):
            for selector in selector_list:
                try:
                    logger.info(f"Trying selector: {selector} with index: {index} (timeout: {timeout}ms)")
                    self.page.locator(selector).nth(index).click(timeout=timeout)
                    logger.info(f"Successfully clicked using selector: {selector} at index: {index}")
                    return
                except Exception as e:
                    logger.info(f"Selector {selector} with index {index} failed: {str(e)}")
                    continue
            raise Exception(f"None of the selectors worked: {selectors} at index: {index}")

    def fill(self, selector: str, text: str):
        with allure.step(f"Fill {text} into {selector}"):
            logger.info(f"Filling '{text}' into '{selector}'")
            self.page.locator(selector).fill(text)

    def fill_with_fallbacks(self, selectors: str, text: str, index: int = 0, timeout: int = 3000):
        """依次尝试多个 selector，填写指定索引处的元素。"""
        selector_list = [s.strip() for s in selectors.split(",")]
        with allure.step(f"Try filling '{text}' into elements: {selectors} (index: {index})"):
            for selector in selector_list:
                try:
                    logger.info(f"Trying selector: {selector} with index: {index} (timeout: {timeout}ms)")
                    self.page.locator(selector).nth(index).fill(text, timeout=timeout)
                    logger.info(f"Successfully filled using selector: {selector} at index: {index}")
                    return
                except Exception as e:
                    logger.info(f"Selector {selector} with index {index} failed: {str(e)}")
                    continue
            raise Exception(f"None of the selectors worked: {selectors} at index: {index}")

    def get_text(self, selector: str) -> str:
        with allure.step(f"Get text from {selector}"):
            text = self.page.locator(selector).text_content()
            logger.info(f"Got text '{text}' from '{selector}'")
            return text # type: ignore

    def get_text_with_fallbacks(self, selectors: str, index: int = 0) -> str:
        """依次尝试多个 selector，获取指定索引处元素的文本。"""
        selector_list = [s.strip() for s in selectors.split(",")]
        with allure.step(f"Try getting text from elements: {selectors} (index: {index})"):
            for selector in selector_list:
                try:
                    logger.info(f"Trying selector: {selector} with index: {index}")
                    text = self.page.locator(selector).nth(index).text_content(timeout=3000)
                    logger.info(f"Successfully got text using selector: {selector} at index: {index}")
                    return text # type: ignore
                except Exception as e:
                    logger.info(f"Selector {selector} with index {index} failed: {str(e)}")
                    continue
            raise Exception(f"None of the selectors worked: {selectors} at index: {index}")

    def wait_for_element(self, selector: str, state="visible", timeout=3000):
        with allure.step(f"Wait for {selector} to be {state}"):
            logger.info(f"Waiting for '{selector}' to be {state}")
            self.page.locator(selector).wait_for(state=state, timeout=timeout) # type: ignore

    def wait_for_element_with_fallbacks(self, selectors: str, state="visible", timeout=3000, index: int = 0):
        """依次尝试多个 selector，等待指定索引处元素达到目标状态。"""
        selector_list = [s.strip() for s in selectors.split(",")]
        with allure.step(f"Try waiting for elements: {selectors} to be {state} (index: {index})"):
            for selector in selector_list:
                try:
                    logger.info(f"Trying selector: {selector} with index: {index}")
                    self.page.locator(selector).nth(index).wait_for(state=state, timeout=timeout) # type: ignore
                    logger.info(f"Successfully waited using selector: {selector} at index: {index}")
                    return
                except Exception as e:
                    logger.info(f"Selector {selector} with index {index} failed: {str(e)}")
                    continue
            raise Exception(f"None of the selectors worked: {selectors} at index: {index}")

    def screenshot(self, path="screenshot.png"):
        with allure.step("Take screenshot"):
            import datetime
            screenshot_dir = load_settings().paths.screenshots_dir
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(path)
            timestamped_path = f"{name}_{timestamp}{ext}"
            screenshot_path = str(screenshot_dir / timestamped_path)
            logger.info(f"Saving screenshot to {screenshot_path}")
            self.page.screenshot(path=screenshot_path)
            with open(screenshot_path, "rb") as image_file:
                allure.attach(image_file.read(), name=timestamped_path, attachment_type=allure.attachment_type.PNG)

    def _collect_page_info(self, context):
        links = self.page.locator("a").all()
        link_texts = [link.text_content() for link in links if link.text_content()]
        link_hrefs = [link.get_attribute("href") for link in links if link.get_attribute("href")]
        allure.attach(f"页面上的链接文本: {link_texts}", name=f"{context} - 链接文本", attachment_type=allure.attachment_type.TEXT)
        allure.attach(f"页面上的链接地址: {link_hrefs}", name=f"{context} - 链接地址", attachment_type=allure.attachment_type.TEXT)

    def _collect_input_info(self, context):
        inputs = self.page.locator("input").all()
        input_info = []
        for inp in inputs:
            input_info.append(
                f"ID: {inp.get_attribute('id') or '无'}, "
                f"类型: {inp.get_attribute('type') or '无'}, "
                f"名称: {inp.get_attribute('name') or '无'}, "
                f"占位符: {inp.get_attribute('placeholder') or '无'}"
            )
        allure.attach(f"页面上的输入框: {input_info}", name=f"{context} - 输入框信息", attachment_type=allure.attachment_type.TEXT)

    def _collect_button_info(self, context):
        buttons = self.page.locator("button").all()
        button_texts = [b.text_content() for b in buttons if b.text_content()]
        button_types = [b.get_attribute("type") for b in buttons if b.get_attribute("type")]
        links = self.page.locator("a").all()
        link_texts = [link.text_content() for link in links if link.text_content()]
        allure.attach(f"页面上的按钮文本: {button_texts}", name=f"{context} - 按钮文本", attachment_type=allure.attachment_type.TEXT)
        allure.attach(f"页面上的按钮类型: {button_types}", name=f"{context} - 按钮类型", attachment_type=allure.attachment_type.TEXT)
        allure.attach(f"页面上的链接文本: {link_texts}", name=f"{context} - 链接文本", attachment_type=allure.attachment_type.TEXT)

    def _collect_page_text(self, context):
        page_text = self.page.inner_text("body")
        allure.attach(f"页面文本内容: {page_text[:2000]}", name=f"{context} - 页面文本", attachment_type=allure.attachment_type.TEXT)

    def click_link_and_switch_to_new_page(self, selectors: str, index: int = 0, timeout: int = 15000, load_state: str = "networkidle"):
        """点击链接打开新页面并切换到新页面。"""
        with allure.step("点击链接打开新页面并切换"):
            try:
                new_page = None
                try:
                    with self.page.expect_popup(timeout=timeout) as popup_info:
                        self.click_with_fallbacks(selectors, index=index)
                    new_page = popup_info.value
                except Exception as popup_exc:
                    logger.info(f"expect_popup 未捕获新页面（可能在当前页导航）: {popup_exc}")
                    try:
                        self.page.wait_for_load_state(load_state, timeout=timeout) # type: ignore
                    except Exception as load_exc:
                        logger.info(f"当前页面未在期望时间内达到 '{load_state}' 状态: {load_exc}")
                    new_page = None

                if new_page:
                    try:
                        new_page.wait_for_load_state(load_state, timeout=timeout) # type: ignore
                    except Exception as e:
                        logger.info(f"新页面未在期望时间内达到 '{load_state}' 状态: {e}.")
                    self.page = new_page
                else:
                    try:
                        self.page.wait_for_load_state(load_state, timeout=timeout) # type: ignore
                    except Exception as e:
                        logger.info(f"点击后当前页面未在期望时间内达到 '{load_state}' 状态: {e}.")

                logger.info(f"当前页面title: {self.page.title()}")
                logger.info(f"当前页面URL: {self.page.url}")
            except Exception as e:
                self._collect_page_info("链接点击")
                raise Exception(f"点击链接打开新页面失败: {str(e)}")

    def restore_original_page(self, original_page):
        """关闭当前（弹出）页并恢复到 original_page。"""
        with allure.step("Close popup and restore original page"):
            try:
                if self.page and self.page is not original_page:
                    try:
                        self.page.close()
                    except Exception as e:
                        logger.info(f"关闭新页面失败: {e}")
                self.page = original_page
                try:
                    self.page.bring_to_front()
                except Exception:
                    pass
            except Exception:
                self._collect_page_info("restore_original_page")
                raise

    @staticmethod
    def _activate_win32_hwnd_preserve_maximize(hwnd: int) -> None:
        """将 Win32 窗口置前；仅在最小化时使用 SW_RESTORE。"""
        if sys.platform != "win32" or not hwnd:
            return
        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)

    def _bring_file_open_dialog_to_front(self) -> None:
        if sys.platform != "win32":
            return
        try:
            from pywinauto import findwindows
        except ImportError:
            return
        user32 = ctypes.windll.user32
        try:
            ASFW_ANY = 0xFFFFFFFF
            user32.AllowSetForegroundWindow(ASFW_ANY)
        except Exception:
            pass
        for title_re in (r".*打开.*", r".*Open.*", r".*浏览.*", r".*Browse.*"):
            try:
                for hwnd in findwindows.find_windows(class_name="#32770", title_re=title_re):
                    try:
                        self._activate_win32_hwnd_preserve_maximize(hwnd)
                        logger.debug("已尝试置前文件选择对话框 hwnd=%s title_re=%s", hwnd, title_re)
                        return
                    except Exception:
                        continue
            except Exception:
                continue
        for title_re in (r".*打开.*", r".*浏览.*", r".*Browse.*"):
            try:
                for hwnd in findwindows.find_windows(title_re=title_re):
                    try:
                        self._activate_win32_hwnd_preserve_maximize(hwnd)
                        return
                    except Exception:
                        continue
            except Exception:
                continue

    def _set_file_dialog_path_and_confirm(self, dialog, file_path):
        """通过 Win32 API 设置文件路径并确认，适用于无人值守环境。"""
        if sys.platform != "win32" or _user32 is None:
            dialog["Edit"].type_keys(file_path)
            dialog["Button"].click()
            return
        edit = dialog["Edit"]
        button = dialog["Button"]
        path_wide = ctypes.c_wchar_p(file_path)
        _user32.SendMessageW(edit.handle, _WM_SETTEXT, 0, path_wide)
        _user32.PostMessageW(button.handle, _BM_CLICK, 0, 0)

    def wait_for_page_complete(self, timeout=20000):
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_function("() => document.readyState === 'complete'", timeout=timeout)

    def wait_for_page_load(self, additional_wait=0):
        try:
            self.page.wait_for_load_state("load")
            if additional_wait > 0:
                self.page.wait_for_timeout(additional_wait)
        except Exception as e:
            logger.error(f"页面加载等待失败: {str(e)}")
            allure.attach(str(e), name="错误信息", attachment_type=allure.attachment_type.TEXT)
            raise
