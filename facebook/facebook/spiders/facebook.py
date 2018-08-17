# -*- coding: utf-8 -*-
import scrapy
import json
# import logging
# import re
from urlparse import urlparse, parse_qs
from scrapy.http import Request, FormRequest
from scrapy.exceptions import CloseSpider
from scrapy.loader import ItemLoader
from ..items import FacebookProfile, Feed
from ..models import get_id


class FacebookSpider(scrapy.Spider):
    name = 'facebook'
    allowed_domains = ['facebook.com']
    facebook_mobile_domain = 'm.facebook.com'
    handle_httpstatus_list = [404, 500]

    def start_requests(self):
        return [
            Request('https://m.facebook.com/login/',
                    callback=self.login)
        ]

    def login(self, response):
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
            facebook_urls = [
                # 'https://www.facebook.com/leon.feng.8',
                # 'https://www.facebook.com/profile.php?id=100011001069493',
                # 'https://www.facebook.com/profile.php?id=100006041015583',
                # 'https://www.facebook.com/vincenzo.sebastiano.98',
                # 'https://www.facebook.com/ancaodobleja',
                # 'https://www.facebook.com/davster3?fref=fr_tab'
                # 'https://www.facebook.com/savannah.edwards1',
                # 'https://www.facebook.com/millina.guaitini',
                # 'https://www.facebook.com/m.holds',
                'https://www.facebook.com/profile.php?id=589566980',
                # 'https://www.facebook.com/byungtae.lee.9',
                # 'https://m.facebook.com/deshen.wang.1'
                ]
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
        yield Request(base_url + 'v=info',
                      callback=self.parse_about_page,
                      meta={
                          'loader': loader,
                          'base_url': base_url,
                          'search_friends_depth': self.settings.get(
                              'SEARCH_FRIENDS_DEPTH', 1),
                          'id': id,
                          'friend_with': response.meta.get('friend_with', None)
                          }
                      )

    def parse_about_page(self, response):
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
                        '(//img[@alt="' + name + '"])[1]/parent::a/@href'
                        ).extract_first()).query)
        except Exception:
            raise CloseSpider('blocked')
        try:
            user_id = query_include_id['id'][0]
        except Exception:
            user_id = query_include_id['profile_id'][0]
        loader.add_value('user_id', user_id)
        # get work
        for work_selector in response.xpath(
                '//div[@id="work"]//div[contains(@id, "u_0")]'):
            work_details = work_selector.xpath(
                '((.//a)[1]/following-sibling::div)[1]//div')
            work_dict = dict([
                ('company', None), ('url', None), ('position', None),
                ('city', None), ('description', None), ('start', None),
                ('end', None)])
            try:
                work_dict['company'] = work_details[0].xpath(
                    './/a/text()').extract_first()
                work_dict['url'] = work_details[0].xpath(
                    './/a/@href').extract_first()
            except Exception:
                pass
            loader.add_value('works', work_dict)

        # education
        for edu_selector in response.xpath(
                '//div[@id="education"]//div[contains(@id, "u_0")]'):
            edu_details = edu_selector.xpath(
                '((.//a)[1]/following-sibling::div)[1]//div')
            edu_dict = dict([
                ('school', None), ('url', None), ('graduated', None),
                ('concentrations', []), ('description', None), ('start', None),
                ('end', None), ('attended_for', None), ('degree', None)])
            try:
                edu_dict['school'] = edu_details[0].xpath(
                    './/a/text()').extract_first()
                edu_dict['url'] = edu_details[0].xpath(
                    './/a/@href').extract_first()
            except Exception:
                pass
            loader.add_value('colleges', edu_dict)

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
        # return loader.load_item()
        # return loader.load_item()
        # response.xpath(
        #     '//span[text()="Works at "]'
        #     ).extract()
        # yield Request()
        # try:
        #     timeline_url = response.xpath(
        #         '//a[text()="Timeline"]/@href').extract()[0]
        # except Exception:
        #     # user may not have a username, use user id
        #     pass
        # try:
        #     friends_url = response.xpath(
        #         '//a[text()="Friends"]/@href').extract()[0]
        # except Exception:
        #     # add v=friends
        #     pass
        # try:
        #     photos_url = response.xpath(
        #         '//a[text()="Photos"]/@href').extract()[0]
        # except Exception:
        #     pass
        # try:
        #     likes_url = response.xpath(
        #         '//a[text()="Likes"]/@href').extract()[0]
        # except Exception:
        #     pass
        # try:
        #     following_url = response.xpath(
        #         '//a[text()="Following"]/@href').extract()[0]
        # except Exception:
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
                "//div[starts-with(@data-ft,'{\"tn\":')]//abbr/text()")
            loader.add_xpath('content', '//title/text()')
            content = loader.get_output_value('content')
            if content == 'Photo':
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
                    # headline = headline.strip() + ' ' + response.xpath(
                    #     '(//div[@id="root"]//table[@role="presentation"])[1]'
                    #     '//strong/following-sibling::a/text()').extract_first()
                    loader.add_value('headline', headline)
                    loader.add_xpath(
                        'links',
                        '(//div[@id="root"]//table[@role="presentation"]'
                        ')[1]//strong/following-sibling::a/@href')
                    location_selector = response.xpath(
                        "//div[starts-with(@data-ft,'{\"tn\":')]"
                        "//abbr/following-sibling::a")
                    if location_selector:
                        loader.add_value('location', {
                            'location': location_selector.xpath(
                                './text()').extract_first(),
                            'url':
                            location_selector.xpath('./@href').extract_first()
                        })
            # print loader.load_item()
            return loader.load_item()
        else:
            pass
