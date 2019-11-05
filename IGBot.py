from igramscraperFIXED.instagram import Instagram
import sys
import socket
import time
import json
import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from createDatabase import Base, Post

class IGBot:
	def __init__ (self, tag="culvercity"):
		self.port = 5000
		self.tag = tag
		self.get_rate = 20
		self.max_sleep = 5
		self.max_age = 10
		self.instagram = Instagram()
		self.foundPosts = {}
		self.startTime = datetime.datetime.now()
		tenMinutesAgo = datetime.datetime.now() - datetime.timedelta(minutes=self.max_age)
		self.latestTimestamp = tenMinutesAgo.timestamp()

		self.connectToDatabase()
		self.startServer()
		self.handleConnection()

	#create socket object which listens for client connection at <port>
	def startServer(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(('', self.port))
		self.socket.listen(5)
		print("Listening on port:",  self.port)


	def connectToDatabase(self):
		engine = create_engine('sqlite:///instagram.db')
		Base.metadata.bind = engine
		DBSession = sessionmaker( bind = engine)
		self.session = DBSession()

	#Waits for client socket connection, upon connection begins to scrape
	def handleConnection(self):
		print("Waiting for client connection")
		while True:
			self.clientsocket, address = self.socket.accept()
			print(f"Connection from {address} has been established!")
			print("Sending new posts from tag:", self.tag)

			while True:
				self.sendNewPosts()

	def sendNewPosts(self):
		recentPosts = self.scrapeInstagram()
		postDicts = self.sendPostsToClient(recentPosts)
		self.savePosts(postDicts)
		self.waitBeforeNextRequest()

	#Retrieves <get_rate> num of posts from <tag>
	def scrapeInstagram(self):
		print("\n--------------------------------------------")
		print("Getting maximum", self.get_rate, "new posts...")
		recPosts = []
		try: 
		    recPosts = self.instagram.get_medias_by_tag(self.tag, count=self.get_rate, min_timestamp=self.latestTimestamp)
		except Exception as e:
		    print("ERROR:", e)
		print("found", len(recPosts), "posts")
		recPosts.reverse()
		return recPosts

	#Convert media objects to dictionaries, scrape usernames from instagram
	def buildPostDict(self, post):
		postDict = {}
		postDict['id'] = post.identifier
		postDict['user_id'] = post.owner.identifier
		postDict['link'] = post.link
		postDict['image'] = post.image_high_resolution_url
		postDict['created_time'] = post.created_time
		postDict['caption'] = post.caption
		try:
			account = self.instagram.get_account_by_id(post.owner.identifier)
			postDict['username'] = account.username
		except Exception as e:
			print("ERROR: failed to get username", e)
		
		return postDict

	#Sends new filtered posts to connected Unity client
	def sendPostsToClient(self, posts):
		if posts:
			print("Sending", len(posts), "points:")
			postDicts = []
			for post in posts:
				postDict = self.buildPostDict(post)
				postDicts.append(postDict)
				self.clientsocket.send(bytes(json.dumps(postDict), "utf-8"))

				print("sending dict:", postDict )
				time.sleep(1)
			return postDicts
		else:
			print("No new posts found...")
			return []

	#saves new post to foundPosts dict and eventually a database, set newest time
	def savePosts(self, postDicts):
		for postDict in postDicts:
			self.foundPosts[postDict['id']] = postDict
			newPost = Post( post_id = postDict['id'],
				  session_start = self.startTime,
				  user_id = postDict['user_id'],
				  link = postDict['link'],
				  image = postDict['image'],
				  created_time = postDict['created_time'],
				  caption = postDict['caption'],
				  username = postDict['username'])
			self.session.add( newPost )
			self.session.commit()
			print("Successfully saved to database")
		print("saving posts...")
		print("total posts scraped:",len(self.foundPosts))
		if postDicts: 
			self.latestTimestamp = postDicts[-1]['created_time'] + 1
			epochDiff = datetime.datetime.now().timestamp() - self.latestTimestamp
			print("Newest post:", "{:.1f}".format(epochDiff/60), "minutes ago")

	#sleep according to <max_sleep>
	def waitBeforeNextRequest(self):
		now = time.localtime().tm_sec % self.max_sleep
		sleep_time = self.max_sleep - now
		print("Sleeping", sleep_time, "seconds")
		time.sleep(sleep_time)

if __name__ == "__main__":
    if len(sys.argv) > 1: 
        IGBot(sys.argv[1])
    else:
        IGBot()
