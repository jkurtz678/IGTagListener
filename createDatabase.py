from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

if __name__ == '__main__':
	engine = create_engine('sqlite:///instagram.db')
	Base.metadata.create_all(engine)