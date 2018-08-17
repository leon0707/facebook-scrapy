import json
from sqlalchemy.orm import sessionmaker
from facebook.models import FacebookUser, Feed, db_connect, create_table
from facebook.items import Feed as FeedItem, FacebookProfile
from dateutil.parser import parse
from datetime import datetime


class saveToSqlite(object):
    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        Creates deals table.
        """
        engine = db_connect()
        create_table(engine)
        self.session = sessionmaker(bind=engine)()

    def process_item(self, item, spider):
        # print item
        session = self.session
        facebook_user = session.query(FacebookUser).filter(
            FacebookUser.id == item['id']).first()
        if isinstance(item, FacebookProfile):
            # print item
            facebook_user.name = item['name']
            facebook_user.facebook_user_name = item.get('user_name', None)
            facebook_user.facebook_user_id = item.get('user_id', None)
            facebook_user.profile_url = item['profile_url']
            facebook_user.current_city = json.dumps(
                item.get('current_city'))
            facebook_user.hometown = json.dumps(item.get('hometown'))
            facebook_user.places_lived = json.dumps(
                item.get('places_lived'))
            facebook_user.colleges = json.dumps(
                item.get('colleges'))
            facebook_user.works = json.dumps(
                item.get('works'))
            facebook_user.fav_quotes = item.get('fav_quotes')
            facebook_user.websites = json.dumps(item.get('websites'))
            facebook_user.mobile_numbers = json.dumps(
                item.get('mobile_numbers'))
            facebook_user.birth_date = item.get('birth_date')
            facebook_user.interested_in = item.get('interested_in')
            facebook_user.gender = item.get('gender')
            session.add(facebook_user)
            if item.get('friend_with', None):
                friend = session.query(FacebookUser).filter(
                    FacebookUser.id == item['friend_with']).first()
                friend.friends.append(facebook_user)
                facebook_user.friends.append(friend)
                session.add(friend)
        elif isinstance(item, FeedItem):
            item.setdefault('headline', '')
            item.setdefault('links', [])
            item.setdefault('location', {})
            # process post_time
            try:
                post_time = parse(item['post_time'])
            except Exception:
                post_time = datetime.now()
            facebook_user.timeline.append(
                Feed(facebook_user_id=item['user_id'],
                     facebook_feed_id=item['feed_id'],
                     content=item['content'],
                     post_time=post_time,
                     feed_url=item['feed_url'],
                     type=item['type'],
                     headline=item['headline'],
                     links=json.dumps(item['links']),
                     location=json.dumps(item['location'])
                     )
                )
            session.add(facebook_user)
        else:
            print item
            pass
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

        return item

    def close_spider(self, spider):
        """Discard the database pool on spider close"""
        self.session.close()
