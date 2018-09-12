"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""

from importlib import import_module

from scrapy import signals
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.http import HtmlResponse
from Cookie import SimpleCookie
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path,
                 driver_arguments, init_url):
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
        self.driver_name = driver_name
        self.driver_executable_path = driver_executable_path
        self.driver_arguments = driver_arguments
        self.init_url = init_url
        self.webdriver_base_path = 'selenium.webdriver.{}'.format(driver_name)

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get(
            'SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get(
            'SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get(
            'SELENIUM_DRIVER_ARGUMENTS', [])
        init_url = crawler.settings.get(
            'SELENIUM_INIT_URL')

        if not driver_name or not driver_executable_path or not init_url:
            raise NotConfigured(
                'SELENIUM_DRIVER_NAME, SELENIUM_DRI'
                'VER_EXECUTABLE_PATH and SELENIUM_INIT_URL must be set'
            )

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            init_url=init_url
        )

        crawler.signals.connect(
            middleware.spider_closed, signals.spider_closed)

        return middleware

    def generate_webdriver(self):
        """Generate a new webdriver."""

        driver_klass_module = import_module(
            '{}.webdriver'.format(self.webdriver_base_path))
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(
            '{}.options'.format(self.webdriver_base_path))
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()
        for argument in self.driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': self.driver_executable_path,
            '{}_options'.format(self.driver_name): driver_options
        }

        driver = driver_klass(**driver_kwargs)
        driver.get(self.init_url)
        return driver

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""
        # print 'SeleniumMiddleware process_request: request ' + str(request)
        if not request.meta.get('enable_selenium', False):
            return None

        cookie = SimpleCookie()
        cookie.load(request.headers.getlist('Cookie')[0])

        driver = self.generate_webdriver()

        for cookie_name, morsel in cookie.items():
            driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': morsel.value
                }
            )

        driver.get(request.url)

        # wait til page loads
        # print driver.find_element_by_tag_name(
        #     'title').get_attribute(
        #         'innerHTML') + ', ' + request.meta['title']
        # print 'compare: ' + str(driver.find_element_by_tag_name(
        #     'title').get_attribute(
        #         'innerHTML') == request.meta['title'])
        # print EC.text_to_be_present_in_element(
        #     (By.TAG_NAME, 'title'), request.meta['title'])
        try:
            element = WebDriverWait(driver, 10).until(
                lambda x: driver.find_element_by_tag_name(
                    'title').get_attribute(
                        'innerHTML') == request.meta['title']
            )
        except TimeoutException:
            raise IgnoreRequest('Cannot open: ' + request.url)

        # print 'waiting ends: ' + request.meta['title']
        body = driver.page_source

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': driver})

        # print 'send response: ' + str(request)

        return HtmlResponse(
            request.url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def process_response(self, request, response, spider):
        # print 'SeleniumMiddleware process_response: request ' + str(request)
        # print 'SeleniumMiddleware process_response: response ' + str(response)
        return response

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""
        # self.driver.quit()
