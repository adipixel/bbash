from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Association

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

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
    user = session.query(User).filter_by(email=login_session['email']).one()
    friends = session.query(Association).filter_by(user_id=user.id).all()
    return jsonify(friends=[i.serialize for i in friends])




@app.route('/profile/<int:id>/')
def viewProfile(id):
    logged_user = getUserInfo(login_session['user_id'])
    friend = session.query(User).filter_by(id=id).one()
    try:
        association = session.query(Association).filter_by(user_id=logged_user.id, friend_id=friend.id).one()
        if association:
            return render_template("friend_profile.html", logged_user=logged_user, user=friend)
    except:
        pass
    return render_template("public_profile.html", logged_user=logged_user, user=friend)

@app.route('/profile/')
def myProfile():
    user = session.query(User).filter_by(email=login_session['email']).one()
    people = session.query(User).all()
    friend_ids = session.query(Association).filter_by(user_id=user.id).all()
    friendList = []
    for f_id in friend_ids:
        friendList.append(session.query(User).filter_by(id=f_id.friend_id).one())

    return render_template("myprofile.html", logged_user=user, people=people, friendList=friendList)

@app.route('/friendRequest/<int:id>', methods=['GET', 'POST'])
def addFriend(id):
    if request.method == 'POST':
        friend = session.query(User).filter_by(id=id).one()
        curUser = session.query(User).filter_by(email=login_session['email']).one()
        association = Association(user_id=curUser.id, friend_id=friend.id, confirmed=1)
        session.add(association)
        session.commit()
        return redirect(url_for('viewProfile', id=id))

@app.route('/unfriend/<int:id>', methods=['GET', 'POST'])
def removeFriend(id):
    if request.method == 'POST':
        friend = session.query(User).filter_by(id=id).one()
        logged_user = getUserInfo(login_session['user_id'])
        association = session.query(Association).filter_by(user_id = logged_user.id, friend_id=friend.id).one()
        session.delete(association)
        session.commit()
        return redirect(url_for('viewProfile', id=id))


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

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
