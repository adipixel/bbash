import random
import string

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import *

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

class Birthday(object):
	"""stores a birthday object"""
	event_id = None
	photos = []
	videos = []
	description = ""
	year = 0

	def __init__(self, event_id, year, description):
		#super(Birthday, self).__init__()
		self.event_id = event_id
		self.photos = getPhotos(event_id)
		#self.videos = getVideos(event_id)
		self.description = description
		self.year = year


def getPhotos(event_id):
	return session.query(Media).filter_by(event_id=event_id, type='photo').all()

def getPhotos(event_id):
	return session.query(Media).filter_by(event_id=event_id, type='video').all()

def getDay(dateStr):
	return dateStr.split('-')[3]

def getMonth(dateStr):
	return dateStr.split('-')[2]

def getYear(dateStr):
	return dateStr.split('-')[0]
