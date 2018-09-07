"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from Cookie import SimpleCookie
# from selenium.webdriver.support.ui import WebDriverWait


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path, driver_arguments):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver

        """

        webdriver_base_path = 'selenium.webdriver.{}'.format(driver_name)

        driver_klass_module = import_module(
            '{}.webdriver'.format(webdriver_base_path))
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(
            '{}.options'.format(webdriver_base_path))
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': driver_executable_path,
            '{}_options'.format(driver_name): driver_options
        }

        self.driver = driver_klass(**driver_kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get(
            'SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get(
            'SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get(
            'SELENIUM_DRIVER_ARGUMENTS', [])

        if not driver_name or not driver_executable_path:
            raise NotConfigured(
                'SELENIUM_DRIVER_NAME and SELENIUM_DRI'
                'VER_EXECUTABLE_PATH must be set'
            )

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(
            middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""
        if not request.meta.get('enable_selenium', False):
            return None

        self.driver.get(request.url)

        cookie = SimpleCookie()
        cookie.load(request.headers.getlist('Cookie')[0])

        for cookie_name, morsel in cookie.items():
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': morsel.value
                }
            )

        self.driver.get(request.url)

        body = self.driver.page_source

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""
        self.driver.quit()