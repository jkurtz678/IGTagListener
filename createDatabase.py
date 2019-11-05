from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy import create_engine

Base = declarative_base()

class Post(Base):
	__tablename__ = 'post'
	id = Column(Integer, primary_key = True)
	session_start = Column(DateTime)
	post_id = Column(Integer)
	user_id = Column(Integer)
	link = Column(String)
	image = Column(String)
	created_time = Column(String)
	caption = Column(String)
	username = Column(String)

if __name__ == '__main__':
	engine = create_engine('sqlite:///instagram.db')
	Base.metadata.create_all(engine)