# -*- coding: utf-8 -*-

# Scrapy settings for facebook project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import os
try:
    # python 3
    from shutil import which
except ImportError:
    # python 2
    from distutils.spawn import find_executable as which

SELENIUM_DRIVER_NAME = 'firefox'
SELENIUM_DRIVER_EXECUTABLE_PATH = which('geckodriver')
SELENIUM_DRIVER_ARGUMENTS = ['--headless']
SELENIUM_INIT_URL = 'https://m.facebook.com'

BOT_NAME = 'facebook'

SEARCH_FRIENDS_DEPTH = 1

LOG_LEVEL = 'INFO'

FACEBOOK_EMAIL = os.environ.get('FACEBOOK_EMAIL')
FACEBOOK_PASS = os.environ.get('FACEBOOK_PASS')

START_FACEBOOK_URL = [
    'https://www.facebook.com/profile.php?id=100004429990971',
    # 'https://www.facebook.com/leon.feng.8',
    # 'https://www.facebook.com/albert.zhang.562',
    # 'https://www.facebook.com/maryxian',
    # 'https://www.facebook.com/bethanyzhangdan',
    # 'https://www.facebook.com/tatkoon',
    # 'https://www.facebook.com/prabuddha.de',
    # 'https://www.facebook.com/bruce.weber.357',
    # 'https://www.facebook.com/cici.li.9',
    # 'https://www.facebook.com/iljoo.kim.712'
    # 'https://www.facebook.com/sara.s.houston',
    # 'https://www.facebook.com/profile.php?id=589566980',
    # 'https://www.facebook.com/jacky.maszeyuen'
    # 'https://www.facebook.com/profile.php?id=100011001069493',
    # 'https://www.facebook.com/profile.php?id=100006041015583',
    # 'https://www.facebook.com/vincenzo.sebastiano.98',
    # 'https://www.facebook.com/ancaodobleja',
    # 'https://www.facebook.com/davster3',
    # 'https://www.facebook.com/savannah.edwards1',
    # 'https://www.facebook.com/ben.chun.3',
    # 'https://www.facebook.com/natalie.criscenzo',
    # 'https://www.facebook.com/lauren.camp.58',
    # 'https://www.facebook.com/andreea.stanica.50',
    # 'https://www.facebook.com/millina.guaitini',
    # 'https://www.facebook.com/m.holds',
    # 'https://www.facebook.com/byungtae.lee.9',
    # 'https://m.facebook.com/deshen.wang.1'
]

SPIDER_MODULES = ['facebook.spiders']
NEWSPIDER_MODULE = 'facebook.spiders'

USER_AGENT = ('Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; '
              'SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, '
              'like Gecko) Version/4.0 Mobile Safari/534.30')

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'

# sqlite
SQLITE_CONNECTION_STRING = 'sqlite:///temp_data.db'

RETRY_HTTP_CODES = [502, 503, 504, 400, 408]

# LOGSTATS_INTERVAL = 10

DOWNLOAD_DELAY = 0.5
# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   # 'facebook.middlewares.test.FacebookSpiderMiddleware': 1,
}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'facebook.middlewares.seleniumMiddleware.SeleniumMiddleware': 800,
    # 'facebook.middlewares.test.FacebookDownloaderMiddleware': 1,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # 'facebook.pipelines.FacebookPipeline': 300,
   'facebook.pipelines.persistDatabase.saveToSqlite': 300
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
