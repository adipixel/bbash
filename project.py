from flask import Flask
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User


app = Flask(__name__)

engine = create_engine('postgresql://birthdaybash:birthdaybash@localhost:5432/bbash')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# read - GET
# update - PUT
# delete - DELETE
# create - POST

@app.route('/')
def index():
    user = session.query(User).all()
    return jsonify(users=[i.serialize for i in user])

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
