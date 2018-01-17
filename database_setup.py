import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine



Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(500))

    @property
    def serialize(self):
        return {
            'name': self.name,
            'email': self.email,
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





engine = create_engine('postgresql://birthdaybash:birthdaybash@localhost:5432/bbash')


Base.metadata.create_all(engine)
