from sqlalchemy import create_engine, Column, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Integer, String, DateTime, Text)
# from sqlalchemy.types import JSON
from sqlalchemy.orm import backref, relationship as dbrelationship, \
    sessionmaker
from scrapy.utils.project import get_project_settings
from datetime import datetime

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(
        get_project_settings().get('SQLITE_CONNECTION_STRING'))


def create_table(engine):
    DeclarativeBase.metadata.create_all(engine)


def get_id(profile_url):
    engine = db_connect()
    create_table(engine)
    session = sessionmaker(bind=engine)()
    facebook_user = session.query(FacebookUser).filter(
        FacebookUser.profile_url == profile_url).first()
    if facebook_user:
        return facebook_user.id
    else:
        facebook_user = FacebookUser(profile_url=profile_url)
        try:
            session.add(facebook_user)
            session.commit()
            return facebook_user.id
        except Exception as e:
            session.rollback()
            raise e


friends_list_table = Table(
    'friends_list', DeclarativeBase.metadata,
    Column('user_id', Integer, ForeignKey('facebook_users.id'),
           primary_key=True),
    Column('friend_with_id', Integer, ForeignKey('facebook_users.id'),
           primary_key=True)
)

likes_list_table = Table(
    'likes_list', DeclarativeBase.metadata,
    Column('user_id', Integer, ForeignKey('facebook_users.id'),
           primary_key=True),
    Column('page_id', Integer, ForeignKey('pages.id'),
           primary_key=True)
)


class FacebookUser(DeclarativeBase):
    __tablename__ = 'facebook_users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column('name', Text())
    facebook_user_name = Column(
        'facebook_user_name', Text(), unique=True, index=True)
    facebook_user_id = Column(
        'facebook_user_id', Text(), unique=True, index=True)
    profile_url = Column('profile_url', Text(), index=True,
                         nullable=False, unique=True)
    works = Column('works', Text())
    colleges = Column('colleges', Text())
    current_city = Column('current_city', Text())
    hometown = Column('hometown', Text())
    places_lived = Column('places_lived', Text())
    fav_quotes = Column('fav_quotes', Text())
    websites = Column('websites', Text())
    mobile_numbers = Column('mobile_numbers', Text())
    birth_date = Column('birth_date', Text())
    interested_in = Column('interested_in', String(16))
    languages = Column('languages', Text())
    religion = Column('religion', Text())
    political = Column('political', Text())
    gender = Column('gender', String(16))
    relationship = Column('relationship', Text())
    life_events = Column('life_events', Text())
    about = Column('life_events', Text())
    timestamp = Column('timestamp', DateTime(), default=datetime.utcnow)
    timeline = dbrelationship('Feed', backref='poster', lazy='dynamic')
    friends = dbrelationship(
        'FacebookUser',
        secondary=friends_list_table,
        primaryjoin=id == friends_list_table.c.user_id,
        secondaryjoin=id == friends_list_table.c.friend_with_id,
        backref=backref('friend_of', lazy='joined'))
    likes = dbrelationship(
        'Page',
        secondary=likes_list_table,
        backref=backref('liked_users', lazy='joined'))

    def __repr__(self):
        return '<FacebookUser: %r, name: %r, profile_url: %r>' \
                % (self.id, self.name,
                   self.profile_url)


class Feed(DeclarativeBase):
    __tablename__ = 'feeds'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('facebook_users.id'),
                     index=True)
    facebook_feed_id = Column('facebook_feed_id', Text(), index=True)
    type = Column('type', String(16))
    content = Column('content', Text())
    facebook_user_id = Column('facebook_user_id', Text(), index=True)
    post_time = Column('post_time', DateTime())
    headline = Column('headline', Text())
    links = Column('links', Text())
    location = Column('location', Text())
    feed_url = Column('feed_url', Text(), nullable=False, unique=True)
    timestamp = Column('timestamp', DateTime(), default=datetime.utcnow)


class Page(DeclarativeBase):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True, index=True)
    facebook_page_id = Column('facebook_page_id', Text(), index=True)
    type = Column('type', String(16))
    name = Column('name', Text())
    page_url = Column('page_url', Text())
    # external_links = Column('external_links', Text())
    timestamp = Column('timestamp', DateTime(), default=datetime.utcnow)
