import random
import string

def getDay(dateStr):
	return dateStr.split('-')[3]

def getMonth(dateStr):
	return dateStr.split('-')[2]

def getYear(dateStr):
	return dateStr.split('-')[0]
