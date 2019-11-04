from igramscraperFIXED.instagram import Instagram
import sys
import socket
import time
import json
import datetime

class IGBot:
	def __init__ (self, tag="culvercity"):
		self.port = 1234
		self.tag = tag
		self.get_rate = 20
		self.max_sleep = 5
		self.max_age = 10
		self.instagram = Instagram()
		self.foundPosts = {}
		tenMinutesAgo = datetime.datetime.now() - datetime.timedelta(minutes=self.max_age)
		self.latestTimestamp = tenMinutesAgo.timestamp()

		self.startServer()
		self.handleConnection()

	#create socket object which listens for client connection at <port>
	def startServer(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((socket.gethostname(), self.port))
		self.socket.listen(5)
		print("Listening on port:",  self.port)

	#Waits for client socket connection, upon connection begins to scrape
	def handleConnection(self):
		print("Waiting for client connection")
		while True:
			self.clientsocket, address = self.socket.accept()
			print(f"Connection from {address} has been established!")
			print("Sending new posts from tag:", self.tag)

			#clientsocket.send(bytes("Connecting established with scraper bot", "utf-8"))
			while True:
				self.sendNewPosts()
		'''
		while True:
			clientsocket, address = self.socket.accept()
			print(f"Connection from {address} has been established!")

			posts = self.getNewPosts(tag)
			print("sending welcome message...");
			clientsocket.send(bytes("Welcome to the server!", "utf-8"))
			while True:
				print("sleeping for 3 seconds");
				time.sleep(3)
				print("sending what's up message...")
				clientsocket.send(bytes("What's up?", "utf-8"))
		'''

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
		#postDict['caption'] = post.caption
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
				#self.clientsocket.send()
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

	def sendNewPosts(self):
		recentPosts = self.scrapeInstagram()
		postDicts = self.sendPostsToClient(recentPosts)
		self.savePosts(postDicts)
		self.waitBeforeNextRequest()

if __name__ == "__main__":
    if len(sys.argv) > 1: 
        IGBot(sys.argv[1])
    else:
        IGBot()
