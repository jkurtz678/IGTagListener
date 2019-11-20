#from igramscraperFIXED.instagram import Instagram
import signal
import sys
import socket
import time
import json
import datetime
import pprint
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from createDatabase import Base, Post
from credentials import username_ig, password_ig
from TargetWatcher import InstaTagWatcher, InstaLocationWatcher
from instagram_private_api.instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
from MyClient import MyClient

class IGBot:
	def __init__ (self, targets):
		self.port = 5000
		self.target_index = 0
		self.num_cycles = 0
		self.get_rate = 20
		self.sleep_time = 5
		self.num_errors = 0

		self.foundPosts = {}
		self.start_time = datetime.datetime.now()

		self.loginInstagram()
		self.connectToDatabase()

	def run(self):
		self.startServer()
		self.handleConnection(targets)

	def loginInstagram(self):
		#self.instagram = Instagram()

		#self.instagram.with_credentials(username_ig, password_ig, '.')
		#self.instagram.login()
		self.api = MyClient(auto_patch=True, authenticate=True, username=username_ig, password=password_ig)


	#create socket object which listens for client connection at <port>
	def startServer(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(('', self.port))
		self.socket.listen(5)
		print("Listening on port:",  self.port)

	def connectToDatabase(self):
		engine = create_engine('sqlite:///instagram.db')
		Base.metadata.bind = engine
		DBSession = sessionmaker( bind = engine)
		self.session = DBSession()

	#Waits for client socket connection, upon connection begins to scrape
	def handleConnection(self, targets):
		'''
		print("Waiting for client connection")
		while True:
			self.clientsocket, address = self.socket.accept()
			print(f"Connection from {address} has been established!")
			print("Queries:", *queries)
		'''

		while True:
			self.processTarget(targets)

	def processTarget(self, targets):
		target = targets[self.target_index]
		posts = self.checkTarget(target)
		self.sendPostsToClient(posts)
		self.savePosts(posts, targets)
		self.num_cycles += 1
		self.waitBeforeNextRequest()

		#update target instagram query
		self.target_index = (self.target_index + 1) % len(targets)

	#Retrieves <get_rate> num of posts from <queries[self.query_index]>
	def checkTarget(self, target):
		print("\n--------------------------------------------")
		print("Session length:", datetime.datetime.now() - self.start_time)
		print("Cycle count:", self.num_cycles)
		print("--------------------------------------------")
		print("Checking target:", target.targetString)
		print("Executing at:", datetime.datetime.now())
		#recPosts = []
		try:
			recPosts = target.scrapeTarget(self.api)
		except:
			print("Error occurred scraping target!")
			self.num_errors += 1
		#print("recPosts", recPosts)
		return recPosts

	#Sends new filtered posts to connected Unity client
	def sendPostsToClient(self, posts):
		if posts:
			for post in posts:
				#self.clientsocket.send(bytes(json.dumps(postDict), "utf-8"))
				print("sending dict:", post )
				time.sleep(1)
		else:
			print("No new posts found...")

	
	#saves new post to foundPosts dict and eventually a database, set newest time
	def savePosts(self, postDicts, targets):
		for postDict in postDicts:
			self.foundPosts[postDict['id']] = postDict
			newPost = Post( post_id = postDict['id'],
				  session_start = postDict['session_start'],
				  query = targets[self.target_index].targetString,
				  user_id = postDict['user_id'],
				  link = postDict['link'],
				  image = postDict['image'],
				  created_time = str(postDict['created_time']),
				  caption = postDict['caption'])
			self.session.add( newPost )
			self.session.commit()
		print("Successfully added posts to database")
		print("Total posts scraped:",len(self.foundPosts))
		print("Total errors encountered:", self.num_errors)			
	
	#sleep according to <sleep_time>
	def waitBeforeNextRequest(self):
		print("Sleeping", self.sleep_time, "seconds")
		time.sleep(self.sleep_time)

if __name__ == "__main__":

	#queries = ['#culvercity', '213420290', '#culvercitystairs']
	#queries = ['#culvercity', '#culvercitystairs']
	#queries = ['#fashion']
	#targets = [InstaTagWatcher('culvercity')]
	targets = [InstaTagWatcher('culvercity'), InstaLocationWatcher('213420290')]

	bot = IGBot(targets)

	def signal_handler(sig, frame):
		end_time = datetime.datetime.now()
		print("\n\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
		#print("Session summary for queries", *queries)
		print("Length of session:", end_time - bot.start_time)
		print("Session start:", bot.start_time)
		print("Session end:", end_time)
		print("Number of cycles", bot.num_cycles)
		print("Total posts scraped:", len(bot.foundPosts ))
		print("Total number of errors:", bot.num_errors)
		sys.exit(0)

	signal.signal(signal.SIGINT, signal_handler)
	bot.run()

	#signal.signal()

