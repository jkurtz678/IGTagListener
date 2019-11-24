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
from instagram_private_api.instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
from MyClient import MyClient
import urllib.request
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class IGBot:
	def __init__ (self, headless=False):
		self.port = 5000
		self.target_index = 0
		self.num_cycles = 0
		self.get_rate = 20
		self.sleep_time = 5
		self.num_errors = 0
		self.foundPosts = {}
		self.start_time = datetime.datetime.now()
		self.headless = headless
		self.clientConnection = False
		#setup interruption handler
		signal.signal(signal.SIGINT, self.signal_handler)

		self.apis = self.setupAPIs()
		self.connectToDatabase()


	def setupAPIs(self):
		print("Connecting to apis...\n")

		#instagram
		instagramClient = MyClient(auto_patch=True, authenticate=True, username=username_ig, password=password_ig)
		
		#twitter
		options = Options()
		options.headless = True
		driver = webdriver.Firefox(options=options)
		
		#add to dict
		return {'twitter': driver, 'instagram': instagramClient}

	def run(self, targets):
		if not self.headless:
			self.startServer()
		self.handleConnection(targets)

	def signal_handler(self, sig, frame):
		end_time = datetime.datetime.now()
		print("\n\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
		print("Length of session:", end_time - self.start_time)
		print("Session start:", self.start_time)
		print("Session end:", end_time)
		print("Number of cycles", self.num_cycles)
		print("Total posts scraped:", len(self.foundPosts ))
		print("Total number of errors:", self.num_errors)
		sys.exit(0)

	#create socket object which listens for client connection at <port>
	def startServer(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(('', self.port))
		self.socket.listen(5)
		print("Listening on port:",  self.port)

	def connectToDatabase(self):
		engine = create_engine('sqlite:///socialmedia.db')
		Base.metadata.bind = engine
		DBSession = sessionmaker( bind = engine)
		self.session = DBSession()

	#Waits for client socket connection, upon connection begins to scrape
	def handleConnection(self, targets):
		if self.headless:
			while True:
				self.processTarget(targets)
		else:
			while True:
				print("\nWaiting for client connection")
				self.clientsocket, address = self.socket.accept()
				print(f"Connection from {address} has been established!")
				self.clientConnection = True
				while self.clientConnection:
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
		print("Platform:",target.platform)
		print("Target:", target.targetString)
		print("Target url:", target.url)
		print("Executing at:", datetime.datetime.now())
		
		try:
			recPosts = target.scrapeTarget(self.apis)
			return recPosts
		except Exception as e:
			print("Error occurred scraping target:", e)
			self.num_errors += 1
			return []

	#Sends new filtered posts to connected client
	def sendPostsToClient(self, posts):
		if posts:
			for post in posts:
				if not self.headless:
					try:
						self.clientsocket.send(bytes(json.dumps(post), "utf-8"))
						print("sending post:", post['link'] )
					except Exception as e:
						print("ERROR: lost connection to client!")
						self.clientConnection = False
				time.sleep(1)
		else:
			print("No new posts found...")
	
	#saves new post to foundPosts dict and eventually a database, set newest time
	def savePosts(self, postDicts, targets):
		for postDict in postDicts:
			self.foundPosts[postDict['id']] = postDict
			newPost = Post( post_id = postDict['id'],
				  session_start = postDict['session_start'],
				  time_scraped = postDict['time_scraped'],
				  query = targets[self.target_index].targetString,
				  user_id = postDict['user_id'],
				  link = postDict['link'],
				  image = postDict['image'],
				  created_time = postDict['created_time'],
				  platform = postDict['platform'],
				  caption = postDict['caption'])
			self.session.add( newPost )
			self.session.commit()
		print("Num posts in response:", len(postDicts))
		print("Successfully added posts to database")
		print("Total posts scraped at target:", targets[self.target_index].postsScraped)
		print("Total posts scraped by bot:",len(self.foundPosts))
		print("Total errors encountered:", self.num_errors)			
	
	#sleep according to <sleep_time>
	def waitBeforeNextRequest(self):
		print("Sleeping", self.sleep_time, "seconds")
		time.sleep(self.sleep_time)
