import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine



Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    dob = Column(String(50))
    picture = Column(String(500))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'dob': self.dob,
        }

class Association(Base):
    __tablename__ = 'association'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    friend_id = Column(Integer)
    confirmed = Column(Integer)
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'confirmed': self.confirmed,
        }

class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    description = Column(String(1000), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    co_user_id = Column(Integer)
    type = Column(String(50), nullable=False)
    year = Column(Integer)
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'co_user_id': self.co_user_id,
            'type': self.type,
            'year': self.year,
            'description': self.description,
        }


class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship(Event)
    url = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)

    @property
    def serialize(self):
        return {
            'event_id': self.event_id,
            'url': self.url,
            'type': self.type,
        }


class Comment(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    media_id = Column(Integer, ForeignKey('media.id'))
    media = relationship(Media)
    dateTime = Column(DateTime)
    text = Column(String(1000))

    @property
    def serialize(self):
        return {
            'media_id': self.media_id,
            'dateTime': self.dateTime,
            'user_id': self.user_id,
            'text': self.text,
        }


class Like(Base):
    __tablename__ = 'Like'

    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, ForeignKey('media.id'))
    media = relationship(Media)
    dateTime = Column(DateTime)
    user_id = Column(Integer, nullable=False)

    @property
    def serialize(self):
        return {
            'media_id': self.media_id,
            'dateTime': self.dateTime,
            'user_id': self.user_id,
        }


class Wish(object):
    __tablename__ = 'wish'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'))
    event = relationship(Event)
    text = Column(String(5000), nullable=False)
    to_user_id = Column(Integer, ForeignKey('user.id'))
    from_user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    media_id = Column(Integer, ForeignKey('media.id'))
    media = relationship(Media)

    @property
    def serialize(self):
        return {
            'event_id': self.event_id,
            'text': self.text,
            'to_user_id': self.to_user_id,
            'from_user_id': self.from_user_id,
            'media_id': self.media_id,
        }








# engine = create_engine('postgresql://birthdaybash:birthdaybash@localhost:5432/bbash')
engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)