from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Association, Event, Comment, Like
from utilities import *

from flask import session as login_session
import random
import string
import os
from werkzeug import secure_filename

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = '14MiIQMR30EnRkv4j-o2FdZd'

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r')
    .read())['web']['client_id']
APPLICATION_NAME = "Birthday Bash"

# Connect to Database and create database session
#engine = create_engine('postgresql://birthdaybash:birthdaybash@localhost:5432/bbash')
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Creating anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Logging in user using oAuth
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validating state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtaining authorization code
    code = request.data

    try:
        # Upgrading the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Checking that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verifing that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verifing that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print
        "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response
        (json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Storing the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Geting user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if user_id is None:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<img class=" img-circle" src="'
    output += login_session['picture']
    output += ''' " style = "width: 200px; height: 200px;"> '''
    output += '<div class="caption text-center"><h2>Welcome, '
    output += login_session['username']
    output += '!</h2></div>'

    flash("you are now logged in as %s" % login_session['username'])
    print
    "done!"
    return output


# Disconnecting the user
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps(
                'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        return redirect(url_for('login'))
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# ------------------------------------------

# read - GET
# update - PUT
# delete - DELETE
# create - POST

@app.route('/profile/')
def myProfile():
    logged_user = getUserInfo(login_session['user_id'])
    friend_ids = session.query(Association).filter_by(user_id=logged_user.id, confirmed=1).all()
    friendList = []
    for f_id in friend_ids:
        friendList.append(session.query(User).filter_by(id=f_id.friend_id).one())
    bdays = session.query(Event).filter_by(type='birthday', user_id=logged_user.id)
    birthdays = []
    for bday in bdays:
        photos = session.query(Media).filter_by(event_id=bday.id, type='photo').all()
        birthdays.append({'id': bday.id, 'year': bday.year, 'description': bday.description, 'photos': photos})

    friend_requests = []
    friend_requests = session.query(Association).filter_by(friend_id=logged_user.id, confirmed=0).all()
    requests = []
    for fr in friend_requests:
        requests.append(session.query(User).filter_by(id=fr.user_id).one())

    return render_template(
        "myprofile.html",
        logged_user=logged_user,
        friendList=friendList,
        birthdays=birthdays,
        requests = requests
        )


@app.route('/profile/update', methods=['GET', 'POST'])
def updateUserProfile():
    logged_user = getUserInfo(login_session['user_id'])
    if request.method == 'GET':
        return render_template("createUserWiz.html", logged_user=logged_user)
    elif request.method == 'POST':
        logged_user.name=request.form['name']
        logged_user.email=request.form['email']
        logged_user.dob=str(request.form['dob'])
        logged_user.picture=request.form['picture']

        session.commit()
        return redirect(url_for('myProfile'))


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = session.query(User).filter_by(email=request.form['email']).one()
        login_session['email'] = user.email
        login_session['name'] = user.name
        return render_template("profile.html", curUser=user)
    else:
        return render_template("login.html")


@app.route('/users')
def getUsers():
    user = session.query(User).all()
    return jsonify(users=[i.serialize for i in user])

@app.route('/friends')
def getFriends():
    user = getUserInfo(login_session['user_id'])
    friends = session.query(Association).filter_by(user_id=user.id).all()
    return jsonify(friends=[i.serialize for i in friends])

@app.route('/events')
def getEvents():
    events = session.query(Event).all()
    return jsonify(events=[i.serialize for i in events])

@app.route('/media')
def getMedia():
    media = session.query(Media).all()
    return jsonify(events=[i.serialize for i in media])



@app.route('/profile/<int:id>/')
def viewProfile(id):
    logged_user = getUserInfo(login_session['user_id'])
    friend = session.query(User).filter_by(id=id).one()
    try:
        association = session.query(Association).filter_by(user_id=logged_user.id, friend_id=friend.id, confirmed=1).one()
        if association:
            bdays = session.query(Event).filter_by(type='birthday', user_id=friend.id)
            birthdays = []
            for bday in bdays:
                photos = session.query(Media).filter_by(event_id=bday.id, type='photo').all()
                birthdays.append({'id': bday.id, 'year': bday.year, 'description': bday.description, 'photos': photos})
            return render_template(
                "friend_profile.html",
                logged_user=logged_user,
                friend=friend,
                birthdays=birthdays)
    except:
        pass
    return render_template("public_profile.html", logged_user=logged_user, friend=friend)

# ---------------------------- friend request -----------------------
@app.route('/friendRequest/<int:id>', methods=['GET', 'POST'])
def addFriend(id):
    if request.method == 'POST':
        friend = session.query(User).filter_by(id=id).one()
        logged_user = getUserInfo(login_session['user_id'])
        try:
            if session.query(Association).filter_by(user_id=logged_user.id, friend_id=friend.id, confirmed=0).one():
                return 'request already sent'
        except Exception as e:
            pass

        association = Association(user_id=logged_user.id, friend_id=friend.id, confirmed=0)
        session.add(association)
        session.commit()
        print "request sent"
        return redirect(url_for('viewProfile', id=id))

@app.route('/unfriend/<int:id>', methods=['GET', 'POST'])
def removeFriend(id):
    if request.method == 'POST':
        friend = session.query(User).filter_by(id=id).one()
        logged_user = getUserInfo(login_session['user_id'])
        association = session.query(Association).filter_by(user_id = logged_user.id, friend_id=friend.id).one()
        session.delete(association)
        session.commit()
        friend_association = session.query(Association).filter_by(user_id = friend.id, friend_id=logged_user.id).one()
        session.delete(friend_association)
        session.commit()
        return redirect(url_for('viewProfile', id=id))

@app.route('/accept/<int:id>', methods=['GET', 'POST'])
def acceptFriend(id):
    if request.method == 'GET':
        friend = session.query(User).filter_by(id=id).one()
        logged_user = getUserInfo(login_session['user_id'])
        association = session.query(Association).filter_by(user_id = friend.id, friend_id=logged_user.id).one()
        association.confirmed = 1
        session.commit()
        newAssociation = Association(user_id=logged_user.id, friend_id=friend.id, confirmed=1)
        session.add(newAssociation)
        session.commit()
        return redirect(url_for('viewProfile', id=id))


@app.route('/decline/<int:id>', methods=['GET', 'POST'])
def declineFriend(id):
    if request.method == 'GET':
        friend = session.query(User).filter_by(id=id).one()
        logged_user = getUserInfo(login_session['user_id'])
        association = session.query(Association).filter_by(user_id=friend.id, friend_id=logged_user.id, confirmed=0).one()
        session.delete(association)
        session.commit()
        return redirect(url_for('myProfile'))


# -----------------------search-------------------------------
@app.route('/search')
def search():
    logged_user = getUserInfo(login_session['user_id'])
    people = session.query(User).all()
    friend_ids = session.query(Association).filter_by(user_id=logged_user.id).all()
    friendList = []
    for f_id in friend_ids:
        friendList.append(session.query(User).filter_by(id=f_id.friend_id).one())

    return render_template("search_results.html", logged_user=logged_user, people=people, friendList=friendList)

@app.route('/')
def index():
    return '<a href="/users">get users</a>'



# ----------------birthday----------------------
@app.route('/create/event', methods=['GET', 'POST'])
def createEvent():
    logged_user = getUserInfo(login_session['user_id'])
    if request.method == 'GET':
        return render_template("create_event.html", logged_user=logged_user)
    elif request.method == 'POST':
        event = Event(
            user_id=logged_user.id,
            co_user_id='',
            type=request.form['type'],
            year=int(request.form['year']),
            description=request.form['description']
            )
        session.add(event)
        session.commit()
        return redirect(url_for('myProfile'))



@app.route('/birthday/<int:user_id>/<int:bday_id>', methods=['GET', 'POST'])
def updateEventData(user_id, bday_id):
    logged_user = getUserInfo(login_session['user_id'])
    if request.method == 'GET':
        event = session.query(Event).filter_by(id=bday_id).one()
        return render_template("add_data_to_event.html", logged_user=logged_user, event=event)


@app.route('/uploadajax/<int:user_id>/<int:event_id>', methods = ['GET', 'POST'])
def upload_file(user_id, event_id):
   if request.method == 'POST':
          f = request.files['file']
          if f:
              extention = "."+(f.filename.split('.')[-1])
              f.filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))+extention
              print f.filename
              filename = secure_filename(f.filename)
              f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
              media = Media(event_id=event_id, type='photo', url=filename)
              session.add(media)
              session.commit()
              return 'file uploaded successfully!'

@app.route('/birthday/update_desc/<int:event_id>', methods = ['GET', 'POST'])
def updateEventDesc(event_id):
   if request.method == 'POST':
          event = session.query(Event).filter_by(id=event_id).one()
          event.description = request.form['desc']
          session.commit()
          return "Saved!"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)