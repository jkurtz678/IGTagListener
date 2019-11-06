from igramscraperFIXED.instagram import Instagram
import signal
import sys
import socket
import time
import json
import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from createDatabase import Base, Post
from credentials import username_ig, password_ig

class IGBot:
	def __init__ (self, queries):
		self.port = 5000
		self.query_index = 0
		self.num_cycles = 0
		self.get_rate = 20
		self.sleep_time = 5
		self.max_age = 10
		self.num_errors = 0

		self.foundPosts = {}
		self.start_time = datetime.datetime.now()
		tenMinutesAgo = datetime.datetime.now() - datetime.timedelta(minutes=self.max_age)
		self.latestTimestamps = [tenMinutesAgo.timestamp() for _ in range(len(queries))]

		self.loginInstagram()
		self.connectToDatabase()

	def run(self):
		self.startServer()
		self.handleConnection(queries)

	def loginInstagram(self):
		self.instagram = Instagram()
		self.instagram.with_credentials(username_ig, password_ig, '.')
		self.instagram.login()

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
	def handleConnection(self, queries):
		print("Waiting for client connection")
		while True:
			self.clientsocket, address = self.socket.accept()
			print(f"Connection from {address} has been established!")
			print("Queries:", *queries)


			while True:
				self.sendNewPosts(queries)

	def sendNewPosts(self, queries):
		recentPosts = self.scrapeInstagram(queries)
		postDicts = self.sendPostsToClient(recentPosts)
		self.savePosts(postDicts, queries)
		self.num_cycles += 1
		self.waitBeforeNextRequest()
		self.query_index = (self.query_index + 1) % len(queries)

	#Retrieves <get_rate> num of posts from <queries[self.query_index]>
	def scrapeInstagram(self, queries):
		print("\n--------------------------------------------")
		print("Executing at:", datetime.datetime.now())
		print("Session length:", datetime.datetime.now() - self.start_time)
		print("Query index:", self.query_index)
		query = queries[self.query_index]
		recPosts = []
		if query[0] == '#':
			recPosts = self.scrapeByTag(query[1:])
		else:
			recPosts = self.scrapeByLocation(query)
		
		recPosts.reverse()
		return recPosts

	def scrapeByTag(self, tag):
		print("Scraping instagram by hashtag: " + tag )
		print("Getting maximum", self.get_rate, "new posts...")

		try: 
			return self.instagram.get_medias_by_tag(tag, count=self.get_rate, min_timestamp=self.latestTimestamps[self.query_index])
		except Exception as e:
			print("ERROR:", e)
			self.num_errors += 1
			return []

	def scrapeByLocation(self, loc_id):
		print("Scraping instagram by location id: " + loc_id)
		print("Getting maximum", self.get_rate, "new posts...")
		posts = []
		try: 
		   	posts = self.instagram.get_medias_by_location_id(loc_id, count=self.get_rate)
		except Exception as e:
			print("ERROR:", e)
			self.num_errors += 1

		posts = [post for post in posts if post.created_time > self.latestTimestamps[self.query_index]]
		return posts

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
			postDict['username'] = "na"
			self.num_errors += 1
		
		return postDict

	#Sends new filtered posts to connected Unity client
	def sendPostsToClient(self, posts):
		if posts:
			print("Found", len(posts), "posts:")
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
	def savePosts(self, postDicts, queries):
		for postDict in postDicts:
			self.foundPosts[postDict['id']] = postDict
			newPost = Post( post_id = postDict['id'],
				  session_start = self.start_time,
				  query = queries[self.query_index],
				  user_id = postDict['user_id'],
				  link = postDict['link'],
				  image = postDict['image'],
				  created_time = postDict['created_time'],
				  caption = postDict['caption'],
				  username = postDict['username'])
			self.session.add( newPost )
			self.session.commit()
		print("Successfully posts to database")
		print("Total posts scraped:",len(self.foundPosts))
		print("Total errors encountered:", self.num_errors)
		if postDicts: 
			self.latestTimestamps[self.query_index] = postDicts[-1]['created_time'] + 1
			epochDiff = datetime.datetime.now().timestamp() - self.latestTimestamps[self.query_index]
			print("Newest post:", "{:.1f}".format(epochDiff/60), "minutes ago")

	#sleep according to <sleep_time>
	def waitBeforeNextRequest(self):
		print("Sleeping", self.sleep_time, "seconds")
		time.sleep(self.sleep_time)

if __name__ == "__main__":

	queries = ['#culvercity', '213420290', '#culvercitystairs']
	#queries = ['#culvercity', '213420290']

	bot = IGBot(queries)

	def signal_handler(sig, frame):
		end_time = datetime.datetime.now()
		print("\n\n\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
		print("Session summary for queries", *queries)
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

