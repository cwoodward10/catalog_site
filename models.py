from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

class SpaceType(Base):
    __tablename__ = 'type of space'

    name = Column(String(250),
                    nullable = False,
                    unique = True,
                    primary_key = True)
    description = Column(String(1000))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
        }

class spaceItem(Base):
    __tablename__ = 'space'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    design_team = Column(String(1000))
    year_built = Column(String(8))
    program = Column(String(250))
    space_type = Column(Integer,
                        ForeignKey('type of space.name'))
    space = relationship(SpaceType)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///catalog_db.db')
Base.metadata.create_all(engine)
