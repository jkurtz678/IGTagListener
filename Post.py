from sqlalchemy import Column, String, Integer
from createDatabase import Base

class Post(Base):
	__tablename__ = 'post'
	id = Column(Integer, primary_key = True)
	post_id = Column(Integer)
	user_id = Column(Integer)
	link = Column(String)
	image = Column(String)
	created_time = Column(String)
	caption = Column(String)
	username = Column(String)