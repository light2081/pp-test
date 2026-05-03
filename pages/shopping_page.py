import allure

from pages.base_page import BasePage
from core.logger import logger


class ShoppingPage(BasePage):
    """购物页面类，封装了购物相关的操作方法"""

    # 页面元素常量
    PRODUCT_NAME = "Sauce Labs Backpack"
    BTN_ADD_TO_CART = "Add to cart"
    CART_ICON = "shopping cart"

    def add_to_cart(self, product_name: str = None) -> None:
        """
        将商品添加到购物车

        :param product_name: 商品名称，默认为预定义的商品名
        """
        target_product = product_name or self.PRODUCT_NAME
        logger.info(f"开始将商品添加到购物车: {target_product}")

        with allure.step(f"点击商品: {target_product}"):
            self.page.get_by_text(target_product).click()
            self.wait_for_page_load()
            logger.debug(f"已点击商品: {target_product}")

        with allure.step(f"点击'添加到购物车'按钮"):
            add_button = self.page.get_by_role("button", name=self.BTN_ADD_TO_CART)
            add_button.wait_for(state="visible", timeout=10000)
            add_button.click()
            self.wait_for_page_load()
            logger.debug("已点击添加到购物车按钮")

        logger.info(f"商品 '{target_product}' 添加到购物车成功")