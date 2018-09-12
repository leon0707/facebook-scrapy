# -*- coding: utf-8 -*-
import scrapy
import json
import re
import datetime
from urlparse import urlparse, parse_qs
from scrapy.http import Request, FormRequest
from scrapy.exceptions import CloseSpider, NotConfigured
from scrapy.loader import ItemLoader
from ..items import FacebookProfile, Feed, Page
from ..models import get_id


class FacebookSpider(scrapy.Spider):
    name = 'facebook'
    allowed_domains = ['facebook.com']
    facebook_mobile_domain = 'm.facebook.com'
    handle_httpstatus_list = [404, 500]

    # degrees = ['PhD', 'Master', 'Ph.D.', 'Bachelor']
    endyear_pattern = re.compile(r'Class of (\d{4})')
    start_end_pattern = re.compile(
        r'([a-zA-Z0-9, ]*\d{4}) - ([a-zA-Z0-9, ]*\d{4}|Present)')
    attended_for = ['College', 'High School']

    def start_requests(self):
        return [
            Request('https://m.facebook.com/login/',
                    callback=self.login)
        ]

    def login(self, response):
        facebook_email = self.settings.get('FACEBOOK_EMAIL')
        password = self.settings.get('FACEBOOK_PASS')
        if not facebook_email or not password:
            raise NotConfigured(
                'FACEBOOK_EMAIL and FACEBOOK_PASS must be set'
            )
        return FormRequest.from_response(
            response,
            formdata={
                'email': self.settings.get('FACEBOOK_EMAIL'),
                'pass': self.settings.get('FACEBOOK_PASS')
            },
            formid='login_form',
            callback=self.device_page
        )

    def device_page(self, response):
        if response.status == 200:
            facebook_urls = self.settings.get('START_FACEBOOK_URL')
            if not facebook_urls:
                raise CloseSpider('No start url')
            for url in facebook_urls:
                url = urlparse(url)._replace(
                    netloc=self.facebook_mobile_domain).geturl()
                yield Request(url,
                              callback=self.parse_homepage)
        else:
            raise CloseSpider('Login Failed')
        # logging.info(response)

    def parse_homepage(self, response):
        loader = ItemLoader(item=FacebookProfile())
        parsed = urlparse(response.url)
        base_url = '{}://{}/{}'.format(parsed.scheme,
                                       parsed.netloc,
                                       filter(bool, parsed.path.split('/'))[0])
        if 'id=' in parsed.query and '/profile.php' in parsed.path:
            loader.add_value(
                'profile_url',
                base_url + '?id=' + parse_qs(parsed.query)['id'][0])
            base_url = base_url + '?id=' + \
                parse_qs(parsed.query)['id'][0] + '&'
            # loader.add_value('user_id', parse_qs(parsed.query)['id'])
        else:
            loader.add_value('profile_url', base_url)
            base_url = base_url + '?'
            loader.add_value('user_name', parsed.path[1:])
            # parse about page
        # get id in the database
        # print loader.get_output_value('profile_url')
        id = get_id(loader.get_output_value('profile_url'))
        loader.add_value('id', id)

        yield Request(url=base_url + 'v=info',
                      callback=self.parse_about_page,
                      priority=1000,
                      meta={
                          'loader': loader,
                          'base_url': base_url,
                          'search_friends_depth': response.meta.get(
                              'search_friends_depth',
                              self.settings.get(
                                  'SEARCH_FRIENDS_DEPTH', 1)),
                          'id': id,
                          'friend_with': response.meta.get(
                              'friend_with', None),
                          'enable_selenium': True,
                          'title': response.xpath(
                              '//title/text()').extract_first()
                          }
                      )

    def parse_about_page(self, response):
        """Parse about page."""

        loader = response.meta['loader']
        name = response.xpath('//title/text()').extract_first()
        if not name:
            print response.url
        loader.add_value('name', name)
        # add user_id
        try:
            query_include_id = parse_qs(
                urlparse(
                    response.xpath(
                        '(//img[@alt="' + name + '"])[1]/ancestor::a/@href'
                        ).extract_first()).query)
        except Exception as e:
            print e
            raise CloseSpider('Cannot find id in: ' + response.url)
        try:
            user_id = query_include_id['id'][0]
        except Exception:
            user_id = query_include_id['profile_id'][0]
        loader.add_value('user_id', user_id)
        # get work
        loader.add_value(
            'works',
            self.extract_work(
                response.xpath(
                    '//div[@id="work"]//div[contains(@id, "u_0")]'),
                response.meta['driver']))

        # education
        loader.add_value(
            'colleges',
            self.extract_edu(
                response.xpath(
                    '//div[@id="education"]//div[contains(@id, "u_0")]'),
                response.meta['driver']))

        response.meta['driver'].quit()

        # skills
        skills_str = response.xpath(
            'string((//div[@id="skills"]/div/div)[2])').extract_first()
        if skills_str:
            skills = skills_str.split(', ')
            skills = skills[:-1] + skills[-1].split(' and ')
            loader.add_value(
                'professional_skills', skills)

        # current_city
        living_div_select = response.xpath('(//div[@id="living"]/div/div)[2]')
        loader.add_value('current_city', {
            'city': living_div_select.xpath(
                './/div[@title="Current City"]//a/text()').extract_first(),
            'page_url': living_div_select.xpath(
                './/div[@title="Current City"]//a/@href').extract_first()
        })
        # hometown
        loader.add_value('hometown', {
            'hometown': living_div_select.xpath(
                './/div[@title="Hometown"]//a/text()').extract_first(),
            'page_url': living_div_select.xpath(
                './/div[@title="Hometown"]//a/@href').extract_first()
        })
        # places_lived
        places_lived_selectors = response.xpath(
            '(//div[@id="living"]/div/div)[2]/div[@title and not(@id)]')
        for places_lived_selector in places_lived_selectors:
            loader.add_value('places_lived', {
                'destination': places_lived_selector.xpath(
                    '(.//a)[2]/text()').extract_first(),
                'page_url': places_lived_selector.xpath(
                    '(.//a)[2]/@href').extract_first(),
                'post_url': places_lived_selector.xpath(
                    '(.//a)[1]/@href').extract_first(),
                'description': places_lived_selector.xpath(
                    '(.//a)[1]/text()').extract_first()
            })
        # contact info
        loader.add_value('websites',
                         response.xpath(
                             '//div[@id="contact-info"]//div'
                             '[@title="Websites"]//a/text()').extract())
        loader.add_value(
            'mobile_numbers',
            response.xpath(
                '(//div[@id="contact-info"]//div[@title="Mobile"]//td)'
                '[2]//span[@dir]/text()').extract())
        # basic info
        loader.add_value(
            'birth_date',
            response.xpath(
                '(//div[@id="basic-info"]//div[@title="Birthday"]//td)'
                '[2]/div/text()').extract_first())
        loader.add_value(
            'gender',
            response.xpath(
                '(//div[@id="basic-info"]//div[@title="Gender"]//td)'
                '[2]/div/text()').extract_first())
        loader.add_value(
            'interested_in',
            response.xpath(
                '(//div[@id="basic-info"]//div[@title="Interested In"]//td)'
                '[2]/div/text()').extract_first())
        loader.add_value(
            'languages',
            filter(
                None,
                re.split(
                    ', | and| language',
                    response.xpath(
                        'string((//div[@id="basic-info"]//div'
                        '[@title="Languages"]//td)[2])').extract_first())))
        loader.add_value(
            'religion',
            {
                'religious_type': response.xpath(
                    'string((//div[@id="basic-info"]//div'
                    '[@title="Religious Views"]//td)[2])').extract_first(),
                'page_url': response.xpath(
                    '(//div[@id="basic-info"]//div[@title="Religious Views"]'
                    '//td)[2]//a/@href').extract_first()
            })
        loader.add_value(
            'political',
            {
                'political_type': response.xpath(
                    'string((//div[@id="basic-info"]//div'
                    '[@title="Political Views"]//td)[2])').extract_first(),
                'page_url': response.xpath(
                    '(//div[@id="basic-info"]//div[@title="Political Views"]'
                    '//td)[2]//a/@href').extract_first()
            })
        # nickname
        for nickname_selector in response.xpath(
                '//div[@id="nicknames"]//div[@title]'):
            loader.add_value(
                'other_names',
                {
                    'type': nickname_selector.xpath(
                        'string((.//td)[1])').extract_first(),
                    'name': nickname_selector.xpath(
                        'string((.//td)[2])').extract_first()
                })
        # relationship
        loader.add_value(
            'relationship',
            {
                'text': response.xpath('string((//div[@id="relationship"]'
                                       '/div/div)[2])').extract_first(),
                'link': response.xpath('(//div[@id="relationship"]/div/div)'
                                       '[2]//a/@href').extract_first()
            })
        # family
        for member_selector in response.xpath(
                '(//div[@id="family"]/div/div)[2]/div/div[1]'):
            loader.add_value(
                'family_members',
                {
                    'name': member_selector.xpath(
                        'string((.//h3)[1])').extract_first(),
                    'relationship': member_selector.xpath(
                        '(.//h3)[2]/text()').extract_first(),
                    'link': member_selector.xpath('.//a/@href').extract_first()
                }
            )

        # about
        loader.add_value(
            'about',
            response.xpath(
                'string((//div[@id="bio"]/div/div)[2])').extract_first())

        # life event
        for event_selector in response.xpath('//div[@id="year-overviews"]//a'):
            loader.add_value(
                'life_events',
                {
                    'headline': event_selector.xpath(
                        './text()').extract_first(),
                    'link': event_selector.xpath(
                        './@href').extract_first()
                }
            )

        # parse quotes
        loader.add_value(
            'fav_quotes',
            response.xpath(
                'string((//div[@id="quote"]/div/div)[2]/div)').extract_first())
        # parse friends page
        if response.meta['search_friends_depth']:
            yield Request(response.meta['base_url'] + 'v=friends',
                          callback=self.parse_friends_page,
                          meta={
                              'loader': loader,
                              'base_url': response.meta['base_url'],
                              'search_friends_depth':
                              response.meta['search_friends_depth'] - 1,
                              'friend_with': response.meta['id']
                              }
                          )
        else:
            loader.add_value('friend_with',
                             response.meta.get('friend_with', None))
        # parse timeline
        yield Request(response.meta['base_url'] + 'v=timeline',
                      callback=self.parse_timeline,
                      meta={
                          'id': response.meta['id'],
                          'user_id': user_id,
                          'base_url': response.meta['base_url']
                          }
                      )
        # parse likes
        yield Request(response.meta['base_url'] + 'v=likes',
                      callback=self.parse_likes,
                      meta={
                          'id': response.meta['id']
                          }
                      )
        loader.add_value('timestamp', datetime.datetime.now())
        # print loader.load_item()
        yield loader.load_item()

    def parse_friends_page(self, response):
        # loader = response.meta['loader']
        friend_selectors = response.xpath(
            '(//h3[contains(text(), "Friends")]/following-sibling::div)'
            '[1]/div//a[text()]')
        for friend_selector in friend_selectors:
            yield Request(
                'https://m.facebook.com' + friend_selector.xpath(
                    './@href').extract_first(),
                callback=self.parse_homepage,
                meta={
                    'friend_with': response.meta['friend_with'],
                    'search_friends_depth':
                    response.meta['search_friends_depth']
                    }
                )
        next_url = response.xpath(
            '//div[@id="m_more_friends"]//a/@href').extract_first()
        if next_url:
            yield Request('https://m.facebook.com' + next_url,
                          callback=self.parse_friends_page,
                          meta={
                              # 'loader': loader,
                              'friend_with': response.meta['friend_with'],
                              'search_friends_depth':
                              response.meta['search_friends_depth']
                              }
                          )

    def parse_timeline(self, response):
        # extract feed
        # self.extract_feed(
        #     response.xpath('//div[@id="structured_composer_async_container"]'
        #                    '//div[@role="article" and @data-ft]'),
        #     response.meta['user_id'])
        for feed in response.xpath('//div[@role="article" '
                                   'and @data-ft]/@data-ft').extract():
            try:
                feed_id = json.loads(feed)['top_level_post_id']
            except Exception:
                feed_id = json.loads(feed)['tl_objid']
            try:
                feed_id = int(feed_id)
            except Exception:
                feed_id = int(feed_id.split(':')[1])
            feed_url = ('https://m.facebook.com/story.'
                        'php?story_fbid={}&id={}').format(
                feed_id, response.meta['user_id'])
            yield Request(feed_url, callback=self.parse_feed,
                          meta={
                              'id': response.meta['id'],
                              'feed_id': feed_id,
                              'user_id': response.meta['user_id']
                          })
        next_url = response.xpath(
            '//*[text()="See More Posts" or '
            'text()="See More Stories"]/parent::a/@href').extract_first()
        if next_url:
            yield Request('https://m.facebook.com' + next_url,
                          callback=self.parse_timeline,
                          meta={
                              'id': response.meta['id'],
                              'user_id': response.meta['user_id']
                              }
                          )

    def parse_feed(self, response):
        if response.status == 200:
            loader = ItemLoader(item=Feed(), response=response)
            loader.add_value('id', response.meta['id'])
            loader.add_value('user_id', response.meta['user_id'])
            loader.add_value('feed_id', response.meta['feed_id'])
            loader.add_value('feed_url', response.url)
            loader.add_xpath(
                'post_time',
                "//div[starts-with(@data-ft,'{\"tn\":')]/div/abbr/text()")
            loader.add_xpath('content', '//title/text()')
            content = loader.get_output_value('content')
            if content == 'Photo' or 'Profile Pictures' or 'Cover Photos':
                # type = 'photo'
                loader.add_value('type', 'photo')
            else:
                if content == 'Comments':
                    # type = 'comments'
                    loader.add_value('type', 'comments')
                else:
                    # type = 'regular'
                    loader.add_value('type', 'regular')
                headline = response.xpath(
                    'string((//div[@id="root"]//table'
                    '[@role="presentation"])[1]//h3)').extract_first()
                if headline:
                    loader.add_value('headline', headline)
                    loader.add_xpath(
                        'links',
                        '(//div[@id="root"]//table[@role="presentation"]'
                        ')[1]//strong/following-sibling::a/@href')
                    location_selector = response.xpath(
                        "//div[starts-with(@data-ft,'{\"tn\":')]"
                        "div/abbr/following-sibling::a")
                    if location_selector:
                        loader.add_value('location', {
                            'location': location_selector.xpath(
                                './text()').extract_first(),
                            'url':
                            location_selector.xpath('./@href').extract_first()
                        })
            loader.add_value('timestamp', datetime.datetime.now())
            return loader.load_item()
        else:
            pass

    def parse_likes(self, response):
        # print response.meta.get('type')
        like_types_selectors = response.xpath(
            '//div[@id="root"]/div/div')
        for like_type_selector in like_types_selectors:
            if response.meta.get('type', False):
                type = response.meta['type']
                if not like_type_selector.xpath(
                        './/*[(self::h3 or self::h4)]/text()').extract_first():
                    # filter the redundent div
                    continue
            else:
                # first time crawl likes page
                type = like_type_selector.xpath(
                    './/*[(self::h3 or self::h4)]/text()').extract_first()
            if type:
                type = type.strip()
                for page_selector in like_type_selector.xpath(
                        './/img'):
                    loader = ItemLoader(item=Page(), response=response)
                    loader.add_value('id', response.meta['id'])
                    loader.add_value('type', type)
                    loader.add_value(
                        'url',
                        page_selector.xpath(
                            '((./following-sibling::div)'
                            '[1]//a)[1]/@href').extract_first())
                    loader.add_value(
                        'name',
                        page_selector.xpath(
                            '((./following-sibling::div)'
                            '[1]//a)[1]//span/text()').extract_first())
                    # print page_selector.xpath(
                    #     '((./following-sibling::div)'
                    #     '[1]//a)[1]//span/text()').extract_first()
                    # extract page id
                    try:
                        loader.add_value(
                            'facebook_page_id',
                            parse_qs(
                                urlparse(
                                    page_selector.xpath(
                                        '(./following-sibling::div)[1]//a'
                                        '[text()="Like"]/@href'
                                        ).extract_first()).query)['id'][0])
                    except Exception:
                        # cannot find like button
                        try:
                            loader.add_value(
                                'facebook_page_id',
                                page_selector.xpath(
                                    './parent::div/parent::div[@id]/@id'
                                    ).extract_first().split(':')[-1])
                        except Exception:
                            # need to process the page to get the id
                            print 'Cannot find id on ' + response.url
                            continue
                    loader.add_value('timestamp', datetime.datetime.now())
                    yield loader.load_item()
                see_more_url = like_type_selector.xpath(
                    './/span[text()="See More"]'
                    '/parent::a/@href').extract_first() or \
                    like_type_selector.xpath(
                        './/a[text()="See More"]/@href').extract_first()
                if see_more_url:
                    yield Request('https://m.facebook.com' + see_more_url,
                                  callback=self.parse_likes,
                                  meta={
                                      'id': response.meta['id'],
                                      'type': type
                                      }
                                  )

    # def extract_feed(self, selectors, user_id):
    #     for feed_selector in selectors:
    #         loader = ItemLoader(item=Feed())
    #         loader.add_value('user_id', user_id)
    #         feed = feed_selector.xpath('./@data-ft').extract_first()
    #         try:
    #             feed_id = json.loads(feed)['top_level_post_id']
    #         except Exception:
    #             feed_id = json.loads(feed)['tl_objid']
    #         try:
    #             feed_id = int(feed_id)
    #         except Exception:
    #             feed_id = int(feed_id.split(':')[1])
    #         loader.add_value('feed_id', feed_id)
    #         loader.add_value(
    #             'content',
    #             feed_selector.xpath(
    #                 "string(.//div[@data-ft='{\"tn\":\"*s\"}'])"
    #                 ).extract_first())
    #     pass

    def extract_edu(self, selector, driver):
        """Extract edu information."""
        edu_list = []
        for counter, edu_selector in enumerate(selector):
            edu_dict = dict([
                ('school', None), ('url', None), ('graduated', None),
                ('concentrations', []), ('description', None), ('start', None),
                ('end', None), ('attended_for', None), ('degree', None)])
            edu_details = edu_selector.xpath(
                '((.//a)[1]/following-sibling::div)[1]/div')
            edu_dict['school'] = edu_details[0].xpath(
                './/a/text()').extract_first()
            edu_dict['url'] = edu_details[0].xpath(
                './/a/@href').extract_first()
            for i in range(1, len(edu_details)):
                text = edu_details[i].xpath(
                    './/span/text()').extract_first()
                # if self.find_match(self.degrees, text):
                #     edu_dict['degree'] = text
                if self.find_match(self.endyear_pattern, text):
                    edu_dict['end'] = self.find_match(
                        self.endyear_pattern, text).group(1)
                elif self.find_match(self.start_end_pattern, text):
                    edu_dict['start'] = self.find_match(
                        self.start_end_pattern, text).group(1)
                    edu_dict['end'] = self.find_match(
                        self.start_end_pattern, text).group(2)
                # elif self.find_match(self.attended_for, text):
                #     edu_dict['attended_for'] = text
                # xpath for selenium
                # either element doesn't have span child or it has a dot span
                xpath_str = ('((((//div[@id="education"]//div'
                             '[contains(@id, "u_0")])[{}]//a)[1]'
                             '/following-sibling::div)[1]/div)'
                             '[{}]//span[not(child::span) or '
                             'child::span[@aria-hidden="true"]]').format(
                    counter + 1, i + 1)
                # selenium element
                try:
                    element = driver.find_elements_by_xpath(xpath_str)[0]
                except IndexError:
                    # print 'url: ' + driver.current_url
                    # print 'selector: ' + selector.xpath('string(.)').extract_first()
                    # print 'xpath_str: ' + xpath_str
                    raise CloseSpider()
                    continue
                if element.value_of_css_property('font-size') == '13px' and \
                        element.value_of_css_property(
                            'color') == 'rgb(128, 128, 128)':
                    # extract concentrations
                    edu_dict['concentrations'] = element.text.split(u'\xb7')
                elif element.value_of_css_property(
                        'color') == 'rgb(75, 79, 86)' and \
                        element.value_of_css_property('font-size') == '12px':
                    # extract degree or attended_for
                    if element.text in self.attended_for:
                        edu_dict['attended_for'] = element.text
                    else:
                        edu_dict['degree'] = element.text
                        edu_dict['attended_for'] = 'Graduate School'
                elif element.value_of_css_property(
                        'color') == 'rgb(29, 33, 41)' and \
                        element.value_of_css_property('font-size') == '12px':
                    edu_dict['description'] = element.text
                if edu_dict['attended_for'] is None:
                    # fill the attend for
                    edu_dict['attended_for'] = 'College'
            edu_list.append(edu_dict)
        return edu_list

    def extract_work(self, selector, driver):
        work_list = []
        for counter, work_selector in enumerate(selector):
            work_details = work_selector.xpath(
                '((.//a)[1]/following-sibling::div)[1]/div')
            work_dict = dict([
                ('company', None), ('url', None), ('position', None),
                ('city', None), ('description', None), ('start', None),
                ('end', None)])
            work_dict['company'] = work_details[0].xpath(
                './/a/text()').extract_first()
            work_dict['url'] = work_details[0].xpath(
                './/a/@href').extract_first()
            for i in range(1, len(work_details)):
                text = work_details[i].xpath(
                    './/span/text()').extract_first()
                if self.find_match(self.start_end_pattern, text):
                    work_dict['start'] = self.find_match(
                        self.start_end_pattern, text).group(1)
                    work_dict['end'] = self.find_match(
                        self.start_end_pattern, text).group(2)
                # extract city
                xpath_str = ('((((//div[@id="work"]//div'
                             '[contains(@id, "u_0")])[{}]//a)[1]'
                             '/following-sibling::div)[1]/div)'
                             '[{}]//span[not(child::span) or '
                             'child::span[@aria-hidden="true"]]').format(
                    counter + 1, i + 1)
                # selenium element
                try:
                    element = driver.find_elements_by_xpath(xpath_str)[0]
                except IndexError:
                    # print 'url: ' + driver.current_url
                    # print 'selector: ' + selector.xpath('string(.)').extract_first()
                    # print 'xpath_str: ' + xpath_str
                    raise CloseSpider()
                    continue
                if element.value_of_css_property(
                        'color') == 'rgb(75, 79, 86)' and \
                        element.value_of_css_property('font-size') == '12px':
                    work_dict['position'] = element.text
                elif element.value_of_css_property(
                        'color') == 'rgb(144, 148, 156)' and \
                        element.value_of_css_property('font-size') == '12px':
                    if work_dict['start'] or work_dict['end']:
                        work_dict['city'] = element.text
                elif element.value_of_css_property(
                        'color') == 'rgb(29, 33, 41)' and \
                        element.value_of_css_property('font-size') == '12px':
                        work_dict['description'] = element.text
            work_list.append(work_dict)
        return work_list

    def find_match(self, match_item, text):
        if isinstance(match_item, list):
            return any(string in text for string in match_item)
        elif isinstance(match_item, re._pattern_type):
            res = match_item.match(text)
            if res:
                return res
            else:
                return False

    # def search_cssRule(self, css, textSelector):
    #     print textSelector
    #     for rule in css.cssRules:
    #         if rule.typeString == 'STYLE_RULE':
    #             print rule.selectorText.replace('.', '')
    #             print rule.style
