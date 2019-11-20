#from instagram_private_api.instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
import reprlib
import code
import datetime

class TargetWatcher:
	def __init__(self, target):
		self.target = target
		self.session_start = datetime.datetime.now()
		self.max_age = 10
		ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=self.max_age)
		self.latest_timestamp = ten_minutes_ago.timestamp()

	def scrapeTarget(self):
		print("values returned for generic: ", self.target)

	def convertResponse(self, responsePosts):
		posts = []
		# filter out posts that have already been found
		recPosts = [post for post in responsePosts if post['node']['taken_at_timestamp'] > self.latest_timestamp]
		
		print("num posts in response:", len(recPosts))
		for post in recPosts:
			postDict = {}
			postDict['id'] = post['node']['id']
			postDict['user_id'] = post['node']['owner']['id']
			postDict['link'] = "https://www.instagram.com/p/" + post['node']['shortcode']
			postDict['query'] = self.targetString
			postDict['image'] = post['node']['display_url']
			postDict['created_time'] = post['node']['taken_at_timestamp']
			postDict['caption'] = post['node']['edge_media_to_caption']['edges'][0]['node']['text']
			postDict['time_scraped'] = datetime.datetime.now()
			postDict['session_start'] = self.session_start
			posts.append(postDict)
		if len(posts) > 0: 
			self.latest_timestamp = posts[0]['created_time']
		epochDiff = datetime.datetime.now().timestamp() - self.latest_timestamp
		print("Newest post:", "{:.1f}".format(epochDiff/60), "minutes ago")


		return posts

	def printKeys(self, dict):
		for key, value in dict.items():
			print(key)


class InstaTagWatcher(TargetWatcher):
	def __init__(self, target, stories=False):
		TargetWatcher.__init__(self,target)
		self.stories=stories
		self.targetString = "instagram:hashtag:" + target

	def scrapeTarget(self, api):
		response = api.tag_feed(self.target, count=10)
		posts = self.convertResponse(response['data']['hashtag']['edge_hashtag_to_media']['edges'])
		return posts

	def printResponse(self, response):
		#print("reels media:",)
		'''
		print("\n\nresponse:")
		self.printKeys(response)
		print("\n\ndata:")
		self.printKeys(response['data'])
		#print("response[data]:", reprlib.repr(response['data']))
		print("\n\nhashtag:")
		self.printKeys(response['data']['hashtag'])
		print("\n\n")
		print("name:", response['data']['hashtag']['name'])
		print("response[hashtag]:", reprlib.repr(response['data']['hashtag']))
		print("response[edge_hashtag_to_media]:", reprlib.repr(response['data']['hashtag']['edge_hashtag_to_media']))
		print("\n\nedge hashtag to media:")
		self.printKeys(response['data']['hashtag']['edge_hashtag_to_media'])
		print("\n\nresponse[edges]:", reprlib.repr(response['data']['hashtag']['edge_hashtag_to_media']['edges']))

		print("\nedges count:", len(response['data']['hashtag']['edge_hashtag_to_media']['edges']))
		print("\nfirst edge", reprlib.repr(response['data']['hashtag']['edge_hashtag_to_media']['edges'][0]['node']))
		self.printKeys(response['data']['hashtag']['edge_hashtag_to_media']['edges'][0]['node'])
		print("shortcode:", response['data']['hashtag']['edge_hashtag_to_media']['edges'][0]['node']['shortcode'])
		print("edge_media_to_caption:", response['data']['hashtag']['edge_hashtag_to_media']['edges'][0]['node']['edge_media_to_caption'])
		'''
		'''
		postDict['id'] = post.identifier
		postDict['user_id'] = post.owner.identifier
		postDict['link'] = post.link
		postDict['query'] = queries[self.target_index]
		postDict['image'] = post.image_high_resolution_url
		postDict['created_time'] = post.created_time
		postDict['caption'] = post.caption
		postDict['session_start'] = self.start_time.timestamp()
		'''
		posts = []
		recPosts = response['data']['hashtag']['edge_hashtag_to_media']['edges']
		#single_node = recPosts[0]['node']
		print("num posts in response:", len(recPosts))
		code.interact(local=locals())

		for post in recPosts:
			postDict = {}
			postDict['id'] = post['node']['id']
			postDict['user_id'] = post['node']['owner']['id']
			postDict['link'] = "https://www.instagram.com/p/" + post['node']['shortcode']
			postDict['query'] = self.targetString 
			postDict['image'] = post['node']['display_url']
			postDict['created_time'] = post['node']['taken_at_timestamp']
			postDict['caption'] = post['node']['edge_media_to_caption']
			postDict['session_start'] = self.start_time.timestamp()
			posts.append(postDict)
		print(posts[2]['link'])
		return posts

	
class InstaLocationWatcher(TargetWatcher):
	def __init__(self, target, stories=False):
		TargetWatcher.__init__(self,target)
		self.stories = stories
		self.targetString = "instagram:location:" + target


	def scrapeTarget(self, api):
		response = api.location_feed(self.target, count=10)
		#code.interact(local=locals())
		posts = self.convertResponse(response['data']['location']['edge_location_to_media']['edges'])
		return posts


#watcher = TagWatcher("culvercity")

#watcher.checkTarget()