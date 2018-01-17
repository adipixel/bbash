#!/usr/bin/python
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User

engine = create_engine('postgresql://birthdaybash:birthdaybash@localhost:5432/bbash')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


user1 = User(name='Aditya', email='adi@gmail.com', picture='')

session.add(user1)
session.commit()

print "Data added!"