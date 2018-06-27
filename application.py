from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base
from flask import session as login_session
import random
import string

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
engine = create_engine('sqlite:///restaurantmenuwithusers.db',
                        connect_args={'check_same_thread':False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

############################  VIEWS GO HERE ##########################################

@app.route('/')
@app.route('/spaces/')
def spacesIndex():
    return 'Welcome to my item catalog.'

@app.route('/spaces/all/')
def allSpaces():
    return 'Here are all the spaces'

@app.route('/spaces/<string:space_name>/')
def spaceTypeView(space_name):
    return 'Here are the spaces in the {} category'.format(space_name)

@app.route('/spaces/create')
def createSpaceType():
    return 'Here is the page to create a new type of space'

@app.route('/spaces/<string:space_name>/edit')
def editSpaceType(space_name):
    return "Here is the page to edit {}'s information".format(space_name)

@app.route('/spaces/<string:space_name>/delete')
def deleteSpaceType(space_name):
    return "Here is the page to delete {}'s information".format(space_name)

@app.route('/spaces/all/<string:space_id>/')
@app.route('/spaces/<string:space_name>/<int:space_id>/')
def spaceItemView(space_id, space_name):
    return "Here is the page to view {}'s information".format(space_id)

@app.route('/spaces/<string:space_name>')
def createSpaceItem(space_name):
    return "Landing page for creating spatial projects"

@app.route('/spaces/<string:space_name>/<string:space_id>/edit')
def editSpaceItem(space_name, space_id):
    return "Landing page for editing {}".format(space_id)

@app.route('/spaces/<string:space_name>/<string:space_id>/delete')
def deleteSpaceItem(space_name, space_id):
    return "Landing page for deleting {}".format(space_id)

############################  INITIATE ##########################################

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
