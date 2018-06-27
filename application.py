from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, SpaceType, SpaceItem
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
engine = create_engine('sqlite:///catalog_db.db',
                        connect_args={'check_same_thread':False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

############################  VIEWS GO HERE ##########################################

@app.route('/')
@app.route('/spaces/')
def spacesIndex():
    space_types = session.query(SpaceType).order_by(asc(SpaceType.name))
    return render_template('index.html', space_types = space_types)

@app.route('/spaces/all/')
def allSpaces():
    spaces = session.query(SpaceItem).order_by(asc(SpaceItem.name))
    return 'Here are all the spaces'

@app.route('/spaces/<string:space_type>/')
def spaceTypeView(space_type):
    spaces = session.query(SpaceItem).filter_by(space_type = space_type)
    return 'Here are the spaces in the {} category'.format(space_type)

@app.route('/spaces/create')
def createSpaceType():
    return 'Here is the page to create a new type of space'

@app.route('/spaces/<string:space_type>/edit')
def editSpaceType(space_type):
    return "Here is the page to edit {}'s information".format(space_type)

@app.route('/spaces/<string:space_type>/delete')
def deleteSpaceType(space_type):
    return "Here is the page to delete {}'s information".format(space_type)

@app.route('/spaces/all/<string:space_id>/')
@app.route('/spaces/<string:space_type>/<int:space_id>/')
def spaceItemView(space_id, space_type):
    return "Here is the page to view {}'s information".format(space_id)

@app.route('/spaces/<string:space_type>')
def createSpaceItem(space_type):
    return "Landing page for creating spatial projects"

@app.route('/spaces/<string:space_type>/<string:space_id>/edit')
def editSpaceItem(space_type, space_id):
    return "Landing page for editing {}".format(space_id)

@app.route('/spaces/<string:space_type>/<string:space_id>/delete')
def deleteSpaceItem(space_type, space_id):
    return "Landing page for deleting {}".format(space_id)

############################  INITIATE ##########################################

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
