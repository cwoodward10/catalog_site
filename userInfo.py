from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, User, SpaceType, SpaceProject
from flask import session as login_session
import random
import string
from functools import wraps


# Connect to Database and create database session
# Allow multi-threading
engine = create_engine('sqlite:///catalog_db.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def createState():
    ''' Creates an object random letters/numbers to help with login '''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    return state


def createUser(login_session):
    ''' Creates a new user for the site when called '''
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    ''' Gathers a particular user's information '''
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    ''' Gathers a particular user's email '''
    user = session.query(User).filter_by(email=email).one_or_none()
    return user.id


def login_required(f):
    ''' Wrapper function for areas of the site that require login '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If a user is logged in, return the view being visited
        if 'username' in login_session:
            return f(*args, **kwargs)
        # If user is not logged in, return the view for the login page
        else:
            flash('Please login to have access here')
            return redirect(url_for('spacesLogin'))
    return decorated_function
