from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    ''' Creates a table that stores a user's information '''
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class SpaceType(Base):
    ''' Creates a table that stores a space type's information '''
    __tablename__ = 'spacetype'

    name = Column(String(250),
                  nullable=False,
                  unique=True,
                  primary_key=True)
    description = Column(String(1000))
    image_url = Column(String(500))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'user_id': self.user_id
        }


class SpaceProject(Base):
    ''' Creates a table that stores a project's information '''
    __tablename__ = 'space'

    id = Column(Integer,
                primary_key=True,
                unique=True)
    name = Column(String(250), nullable=False)
    design_team = Column(String(1000))
    year_built = Column(String(8))
    program = Column(String(250))
    image_url = Column(String(500))
    space_type = Column(String(250),
                        ForeignKey('spacetype.name'))
    space = relationship(SpaceType)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'design_team': self.design_team,
            'year_built': self.year_built,
            'program': self.program,
            'image_url': self.image_url,
            'space_type': self.space_type,
            'user_id': self.user_id
        }


engine = create_engine('postgresql://catalog:catalogHere@localhost/catalog')
Base.metadata.create_all(engine)
