import sys
import os
import pytest

from core.logger import logger
from core.settings import load_settings
from core.data_loader import read_yaml

# 将项目根目录添加到sys.path，解决ModuleNotFoundError问题
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import Page, expect
from pages.shopping_page import ShoppingPage
import allure


@allure.feature("购物")
@allure.story("购物-添加购物车")
@allure.tag("regression")
@pytest.mark.regression
class TestAddCart:

    @allure.title("购物-添加购物车")
    @allure.description("测试将商品添加到购物车功能")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_to_cart(self, page: Page):
        """
        测试步骤：
        1. 点击指定商品进入详情页
        2. 点击'添加到购物车'按钮
        3. 验证购物车数量更新
        """
        logger.info("========== 开始执行测试: 添加购物车 ==========")

        # 加载配置
        settings = load_settings()
        shopping_page = ShoppingPage(page)

        # 使用测试数据文件中的商品名称
        testdata = read_yaml("add_to_cart.yaml")
        product_name = testdata["product_name"]
        logger.info(f"待添加商品: {product_name}")

        with allure.step(f"将商品 '{product_name}' 添加到购物车"):
            shopping_page.add_to_cart(product_name)

        with allure.step("验证购物车数量"):
            # 验证购物车图标显示数量
            cart_badge = page.locator("span.shopping_cart_badge")
            expect(cart_badge).to_have_text("1", timeout=10000)
            logger.info("购物车数量验证成功")

        logger.info("========== 测试完成: 添加购物车 ==========")