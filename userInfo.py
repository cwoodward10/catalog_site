from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, User, SpaceType, SpaceProject
from flask import session as login_session
import random
import string


# Connect to Database and create database session
# Allow multi-threading
engine = create_engine('sqlite:///catalog_db.db',
                        connect_args={'check_same_thread':False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def createState():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    return state

def createUser(login_session):
    newUser = User(name = login_session['username'],
                    email = login_session['email'],
                    picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None
