# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.loader.processors import TakeFirst


class FacebookProfile(Item):
    id = Field(output_processor=TakeFirst())
    name = Field(output_processor=TakeFirst())
    user_name = Field(output_processor=TakeFirst())
    user_id = Field(output_processor=TakeFirst())
    profile_url = Field(output_processor=TakeFirst())

    # list {company, url, position, city, description, start, end, past}
    works = Field()
    # list {project, with [], description, start, end}
    projects = Field()
    professional_skills = Field()  # list {skill, page_url}
    # list {school, url, start, end, graduated, description,
    # concentrations [], attended for, degree}
    colleges = Field()
    # list {school, start, end, graduated, description}
    # high_school = Field()

    current_city = Field(output_processor=TakeFirst())  # json {city, page_url}
    hometown = Field(output_processor=TakeFirst())  # json {hometown, page_url}
    # list {destination, page_url, post_url, description}
    places_lived = Field()

    mobile_numbers = Field()  # list
    address = Field()  # string
    neighborhood = Field()  # string
    email = Field()  # string
    websites = Field()  # list
    social_links = Field()  # list
    birth_date = Field(output_processor=TakeFirst())  # string
    # birth_year = Field()  # int
    gender = Field(output_processor=TakeFirst())  # string
    interested_in = Field(output_processor=TakeFirst())  # string
    languages = Field()  # list {language, page_url}
    # json {religious_type, description, page_url}
    religion = Field(output_processor=TakeFirst())
    # json {political_type, description, page_url}
    political = Field(output_processor=TakeFirst())

    # {relationship_status, partner_name, partner_profile_url, time}
    relationship = Field(output_processor=TakeFirst())
    family_members = Field()  # list {name, relationship, profile_url}

    about = Field()  # string
    name_pronunciation = Field()  # mp3 url
    other_names = Field()  # list { type: '', name: ''}
    fav_quotes = Field(output_processor=TakeFirst())  # string

    life_events = Field()  # list {event_title, post_url}

    # friend_groups = Field()  # list {group_name, group_url}
    # friends = Field()  # list {name, profile_url}
    # number_friends = Field(output_processor=TakeFirst())
    friend_with = Field(output_processor=TakeFirst())

    likes = Field()


class Feed(Item):
    id = Field(output_processor=TakeFirst())
    user_id = Field(output_processor=TakeFirst())
    feed_id = Field(output_processor=TakeFirst())
    content = Field(output_processor=TakeFirst())
    type = Field(output_processor=TakeFirst())
    post_time = Field(output_processor=TakeFirst())
    feed_url = Field(output_processor=TakeFirst())
    links = Field()
    headline = Field(output_processor=TakeFirst())
    location = Field(output_processor=TakeFirst())  # {location, link}


class Page(Item):
    id = Field(output_processor=TakeFirst())
    facebook_page_id = Field(output_processor=TakeFirst())
    type = Field(output_processor=TakeFirst())
    name = Field(output_processor=TakeFirst())
    url = Field(output_processor=TakeFirst())
    external_links = Field()
