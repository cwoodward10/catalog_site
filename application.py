from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, SpaceType, SpaceProject
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
def spacesIndex():
    space_types = session.query(SpaceType).order_by(asc(SpaceType.name)).all()
    return render_template('index.html', space_types = space_types)

@app.route('/spaces/all')
def allSpaces():
    spaces = session.query(SpaceProject).order_by(asc(SpaceProject.name)).all()
    return render_template('spacetype_all.html', spaces = spaces)

@app.route('/spaces/<string:space_type>')
def spaceTypeView(space_type):
    spaces = session.query(SpaceProject).filter_by(space_type =
                                                    space_type).all()
    spaceType = session.query(SpaceType).filter_by(name = space_type).one()
    return render_template('spacetype_specific.html',
                            spaces = spaces,
                            spaceType = spaceType)

@app.route('/spaces/create', methods = ['GET', 'POST'])
def createSpaceType():
    if request.method == 'POST':
        newType = SpaceType(name = request.form['name'],
                            description = request.form['description'])
        try:
            session.add(newType)
            session.commit()
            flash('New type of space named {} created'.format(newType.name))
            return redirect(url_for('spacesIndex'))
        except:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('spacetype_new.html')

    else:
        return render_template('spacetype_new.html')

@app.route('/spaces/<string:space_type>/edit', methods=['GET', 'POST'])
def editSpaceType(space_type):
    editted_space = session.query(SpaceType).filter_by(name = space_type).one()
    if request.method == 'POST':
        if request.form['name']:
            editted_space.name = request.form['name']
        if request.form['description']:
            editted_space.description = request.form['description']
        try:
            session.add(editted_space)
            session.commit()
            flash('Success: {} has been editted'.format(editted_space.name))
            return redirect(url_for('spaceTypeView', space_type = space_type))
        except:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('spacetype_edit.html',
                                    space = editted_space)
    else:
        return render_template('spacetype_edit.html',
                                space = editted_space)

@app.route('/spaces/<string:space_type>/delete', methods=['GET', 'POST'])
def deleteSpaceType(space_type):
    deleted_space = session.query(SpaceType).filter_by(name = space_type).one()
    if request.method == 'POST':
        try:
            session.delete(deleted_space)
            name = deleted_space.name
            session.commit()
            flash('Successfully deleted {}'.format(name))
            return redirect(url_for('spacesIndex'))
        except:
            session.rollback()
            flash('There was a problem in deleting the project')
            return render_template('spacetype_delete.html',
                                    spaceType = deleted_space)
    else:
        return render_template('spacetype_delete.html',
                                spaceType = deleted_space)

@app.route('/spaces/<string:space_type>/<int:space_id>/')
def spaceProjectView(space_id, space_type):
    space = session.query(SpaceProject).filter_by(id = space_id).one()
    return render_template('project_specific.html', space = space)

@app.route('/spaces/all/create', methods = ['GET', 'POST'])
@app.route('/spaces/<string:space_type>/create', methods = ['GET', 'POST'])
def createSpaceProject(space_type = None):
        if space_type != None:
            space = session.query(SpaceType).filter_by(name = space_type).one()
        else:
            space = None
        space_types = session.query(SpaceType).all()
        if request.method == 'POST':
            newProject = SpaceProject(name = request.form['name'],
                                design_team  = request.form['design_team'],
                                year_built = request.form['year_built'],
                                program = request.form['program'],
                                space_type = request.form['space_type']
                                )
            try:
                session.add(newProject)
                session.commit()
                flash('New type of project named {} was created'.format(newProject.name))
                return redirect(url_for('spaceTypeView',
                                        space_type = newProject.space_type))
            except:
                session.rollback()
                flash('Failed to create a new project.')
                return render_template('project_new.html',
                                        space_types = space_types,
                                        space = space)

        else:
            return render_template('project_new.html',
                                    space_types = space_types,
                                    space = space)

@app.route('/spaces/<string:space_type>/<string:space_id>/edit'
            , methods=['GET', 'POST'])
def editSpaceProject(space_type, space_id):
    editted_proj = session.query(SpaceProject).filter_by(id = space_id).one()
    space_types = session.query(SpaceType).order_by(asc(SpaceType.name)).all()
    if request.method == 'POST':
        if request.form['name']:
            editted_proj.name = request.form['name']
        if request.form['design_team']:
            editted_proj.design_team = request.form['design_team']
        if request.form['year_built']:
            editted_proj.year_built = request.form['year_built']
        if request.form['program']:
            editted_proj.program = request.form['program']
        if request.form['space_type']:
            editted_proj.space_type = request.form['space_type']
            space_type_new = editted_proj.space_type

        try:
            session.add(editted_proj)
            session.commit()
            flash('Success: {} has been editted'.format(editted_proj.name))
            return redirect(url_for('spaceProjectView',
                                    space_type = space_type,
                                    space_id = space_id))
        except:
            session.rollback()
            flash('Failed to create a new type of space.')
            return render_template('project_edit.html',
                                    project = editted_proj,
                                    space_types = space_types)
    else:
        return render_template('project_edit.html',
                                project = editted_proj,
                                space_types = space_types)

@app.route('/spaces/<string:space_type>/<string:space_id>/delete'
            , methods=['GET', 'POST'])
def deleteSpaceProject(space_type, space_id):
        deleted_project = session.query(SpaceProject).filter_by(id = space_id).one()
        if request.method == 'POST':
            try:
                session.delete(deleted_project)
                name = deleted_project.name
                session.commit()
                flash('Successfully deleted {}'.format(name))
                return redirect(url_for('spaceTypeView', space_type = space_type))
            except:
                session.rollback()
                flash('There was a problem in deleting the project')
                return render_template('project_delete.html',
                                        space_project = deleted_project)
        else:
            return render_template('project_delete.html',
                                    space_project = deleted_project)

############################  INITIATE ##########################################

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
