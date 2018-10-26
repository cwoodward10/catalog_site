from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from models import Base, User, SpaceType, SpaceProject
from userInfo import createUser, getUserInfo, getUserID, createState
from userInfo import login_required
from flask import session as login_session
import random
import string
import os
from functools import wraps

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Spaces Catalog Application"

# Connect to Database and create database session
# Allow multi-threading
engine = create_engine('postgresql://catalog:catalogHere@localhost/catalog',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# -------------------------------VIEWS GO HERE---------------------------------


@app.route('/')
@app.route('/spaces/')
def spacesIndex():
    space_types = session.query(SpaceType).order_by(asc(SpaceType.name)).all()
    if 'username' not in login_session:
        login_state = False
    else:
        login_state = True
    return render_template('index.html',
                           space_types=space_types,
                           login_state=login_state)


@app.route('/spaces/login')
def spacesLogin():
    state = createState()
    login_session['state'] = state
    return render_template('login.html', state=state, CLIENT_ID=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    ''' Handles the login validation from Google Login API '''
    # Note:I took this from the Udacity Code
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(access_token))  # noqa
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode())
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                   json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '    # noqa
    flash("you are now logged in as {}".format(login_session['username']))
    print("done!")
    return output


@app.route('/logout')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        output = ''
        output += '<p>Current user not connected.</p>'
        output += "<a href='/space/'>Go Back</a>"
        print('Access Token is None')
        response = make_response(json.dumps(output), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is {}'.format(access_token))
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(login_session['access_token'])    # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        output = ''
        output += 'Successfully disconnected.'
        output += "<a href='/spaces/'>Go Back</a>"
        return output
    else:
        output = ''
        output += 'Failed to revoke token for given user.'
        response = make_response(json.dumps(output, 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/spaces/all')
def allSpaces():
    spaces = session.query(SpaceProject).order_by(asc(SpaceProject.name)).all()
    if 'username' not in login_session:
        login_state = False
    else:
        login_state = True
    return render_template('spacetype_all.html',
                           spaces=spaces,
                           login_state=login_state)


@app.route('/spaces/<string:space_type>')
def spaceTypeView(space_type):
    spaces = session.query(SpaceProject).filter_by(space_type=space_type).all()
    spaceType = session.query(SpaceType).filter_by(
                name=space_type).one_or_none()
    creator = getUserInfo(spaceType.user_id)
    if 'username' not in login_session:
        creator_state = False
        login_state = False
    elif creator.id != login_session['user_id']:
        login_state = True
        creator_state = False
    else:
        login_state = True
        creator_state = True
    return render_template('spacetype_specific.html',
                           spaces=spaces,
                           spaceType=spaceType,
                           creator_state=creator_state,
                           login_state=login_state)


@app.route('/spaces/create', methods=['GET', 'POST'])
@login_required
def createSpaceType():
    ''' Creates a view that allows a user create a new space type. '''
    if request.method == 'POST':
        newType = SpaceType(name=request.form['name'],
                            description=request.form['description'],
                            image_url=request.form['image_url'],
                            user_id=login_session['user_id'])
        try:
            session.add(newType)
            session.commit()
            flash('New type of space named {} created'.format(newType.name))
            return redirect(url_for('spacesIndex', login_state=True))
        # Rollback changes if any errors occur
        except exc.IntegrityError:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('spacetype_new.html', login_state=True)

    else:
        return render_template('spacetype_new.html')


@app.route('/spaces/<string:space_type>/edit', methods=['GET', 'POST'])
@login_required
def editSpaceType(space_type):
    '''Creates a view that allows a user to edit a space type's information'''
    editted_space = session.query(SpaceType).filter_by(
                    name=space_type).one_or_none()
    if editted_space.user_id != login_session['user_id']:
        return '''<script> function myFuction() {alert('You are not authorized
                to edit this type of space. Please create your own type in
                order to edit.');}</script><body onload='myFuction()''>
                '''
    if request.method == 'POST':
        if request.form['name']:
            editted_space.name = request.form['name']
        if request.form['description']:
            editted_space.description = request.form['description']
        if request.form['image_url']:
            editted_space.image_url = request.form['image_url']
        try:
            session.add(editted_space)
            session.commit()
            flash('Success: {} has been editted'.format(editted_space.name))
            return redirect(url_for('spaceTypeView',
                                    space_type=editted_space.name))
        except exc.IntegrityError:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('spacetype_edit.html',
                                   space=editted_space,
                                   login_state=True)
    else:
        return render_template('spacetype_edit.html',
                               space=editted_space,
                               login_state=True)


@app.route('/spaces/<string:space_type>/delete', methods=['GET', 'POST'])
@login_required
def deleteSpaceType(space_type):
    ''' Creates a view for confirming the deletion of a space type '''
    deleted_space = session.query(SpaceType).filter_by(
                    name=space_type).one_or_none()
    if deleted_space.user_id != login_session['user_id']:
        return '''<script> function myFuction() {alert('You are not authorized
                to delete this type of space. Please create your own type in
                order to delete.');}</script><body onload='myFuction()''>
                '''
    if request.method == 'POST':
        try:
            session.delete(deleted_space)
            name = deleted_space.name
            session.commit()
            flash('Successfully deleted {}'.format(name))
            return redirect(url_for('spacesIndex', login_state=True))
        except exc.IntegrityError:
            session.rollback()
            flash('There was a problem in deleting the project')
            return render_template('spacetype_delete.html',
                                   spaceType=deleted_space,
                                   login_state=True)
    else:
        return render_template('spacetype_delete.html',
                               spaceType=deleted_space,
                               login_state=True)


@app.route('/spaces/<string:space_type>/<int:space_id>/')
def spaceProjectView(space_id, space_type):
    space = session.query(SpaceProject).filter_by(id=space_id).one_or_none()
    creator = getUserInfo(space.user_id)
    if 'username' not in login_session:
        creator_state = False
        login_state = False
    elif creator.id != login_session['user_id']:
        login_state = True
        creator_state = False
    else:
        creator_state = True
        login_state = True
    return render_template('project_specific.html',
                           space=space,
                           creator_state=creator_state,
                           login_state=login_state)


@app.route('/spaces/all/create', methods=['GET', 'POST'])
@app.route('/spaces/<string:space_type>/create', methods=['GET', 'POST'])
@login_required
def createSpaceProject(space_type=None):
    ''' Creates a view that allows a user to create a new project. '''
    if space_type is not None:
        space = session.query(SpaceType).filter_by(
                name=space_type).one_or_none()
    else:
        space = None
    space_types = session.query(SpaceType).all()
    if request.method == 'POST':
        newProject = SpaceProject(name=request.form['name'],
                                  design_team=request.form['design_team'],
                                  year_built=request.form['year_built'],
                                  program=request.form['program'],
                                  image_url=request.form['image_url'],
                                  space_type=request.form['space_type'],
                                  user_id=login_session['user_id']
                                  )
        try:
            session.add(newProject)
            session.commit()
            flash('New type of project named {} was created'.format(newProject.name))  # noqa
            return redirect(url_for('spaceTypeView',
                                    space_type=newProject.space_type,
                                    login_state=True))
        except exc.IntegrityError:
            session.rollback()
            flash('Failed to create a new project.')
            return render_template('project_new.html',
                                   space_types=space_types,
                                   space=space,
                                   login_state=True)

    else:
        return render_template('project_new.html',
                               space_types=space_types,
                               space=space,
                               login_state=True)


@app.route('/spaces/<string:space_type>/<string:space_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editSpaceProject(space_type, space_id):
    ''' Creates a view that allows a user to edit a project's information '''
    editted_proj = session.query(SpaceProject).filter_by(
                   id=space_id).one_or_none()
    space_types = session.query(SpaceType).order_by(asc(SpaceType.name)).all()
    if editted_proj.user_id != login_session['user_id']:
        return '''<script> function myFuction() {alert('You are not authorized
                to edit this project. Please create your own project in
                order to edit.');}</script><body onload='myFuction()''>
                '''
    if request.method == 'POST':
        if request.form['name']:
            editted_proj.name = request.form['name']
        if request.form['design_team']:
            editted_proj.design_team = request.form['design_team']
        if request.form['year_built']:
            editted_proj.year_built = request.form['year_built']
        if request.form['program']:
            editted_proj.program = request.form['program']
        if request.form['image_url']:
            editted_proj.image_url = request.form['image_url']
        if request.form['space_type']:
            editted_proj.space_type = request.form['space_type']
            space_type_new = editted_proj.space_type

        try:
            session.add(editted_proj)
            session.commit()
            flash('Success: {} has been editted'.format(editted_proj.name))
            return redirect(url_for('spaceProjectView',
                                    space_type=space_type,
                                    space_id=space_id,
                                    login_state=True))
        except exc.IntegrityError:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('project_edit.html',
                                   project=editted_proj,
                                   space_types=space_types,
                                   login_state=True)
    else:
        return render_template('project_edit.html',
                               project=editted_proj,
                               space_types=space_types,
                               login_state=True)


@app.route('/spaces/<string:space_type>/<string:space_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteSpaceProject(space_type, space_id):
    ''' Creates a view for confirming the deletion of a project '''
    deleted_proj = session.query(SpaceProject).filter_by(
                   id=space_id).one_or_none()
    if deleted_proj.user_id != login_session['user_id']:
        return '''<script> function myFuction() {alert('You are not authorized
                to delete this project. Please create your own project in
                order to delete.');}</script><body onload='myFuction()''>
                '''
    if request.method == 'POST':
        try:
            session.delete(deleted_proj)
            name = deleted_project.name
            session.commit()
            flash('Successfully deleted {}'.format(name))
            return redirect(url_for('spaceTypeView',
                                    space_type=space_type,
                                    login_stat=True))
        except exc.IntegrityError:
            session.rollback()
            flash('There was a problem in deleting the project')
            return render_template('project_delete.html',
                                   space_project=deleted_proj,
                                   login_state=True)
        else:
            return render_template('project_delete.html',
                                   space_project=deleted_proj,
                                   login_state=True)


# -------------------------API ENDPOINTS GO HERE-------------------------------


@app.route('/spaces/<string:space_type>/JSON')
def spaceTypeJSON(space_type):
    space_type = session.query(SpaceType).filter_by(
                 name=space_type).one_or_none()
    return jsonify(Space_Type=space_type.serialize)


@app.route('/spaces/<string:space_type>/<int:space_id>/JSON')
def spaceProjectJSON(space_type, space_id):
    space = session.query(SpaceProject).filter_by(id=space_id).one_or_none()
    return jsonify(Space=space.serialize)


# ---------------------------INITIATE------------------------------------------


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
