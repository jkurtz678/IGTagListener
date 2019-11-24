from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
from sqlalchemy import create_engine

Base = declarative_base()

class Post(Base):
	__tablename__ = 'post'
	id = Column(Integer, primary_key = True)
	session_start = Column(Integer)
	time_scraped = Column(Integer)
	created_time = Column(Integer)
	post_id = Column(Integer)
	user_id = Column(Integer)
	query = Column(String)
	platform = Column(String)
	link = Column(String)
	image = Column(String)
	caption = Column(String)
	username = Column(String)

if __name__ == '__main__':
	engine = create_engine('sqlite:///socialmedia.db')
	Base.metadata.create_all(engine)