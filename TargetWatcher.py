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

	def convertInstagramResponse(self, responsePosts):
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

	def convertTwitterResponse(self, responseTweets):
		media = []
		recTweets = [tweet for tweet in responseTweets if tweet.timestamp_epochs > self.latest_timestamp]
		print("num new tweets found:", len(recTweets) )
		print("first link:", 'https://www.twitter.com' + responseTweets[0].tweet_url)
		code.interact(local=locals())

		for tweet in recTweets:
			tweetDict = {}
			tweetDict['id'] = tweet.tweet_id
			tweetDict['user_id'] = tweet.user_id
			tweetDict['link'] = 'https://www.twitter.com' + tweet.tweet_url
			tweetDict['query'] = self.targetString
			img_str = ""
			for img_url in tweet.img_urls:
				img_str += (img_url + " ")
			if len(img_str) > 0:
				img_str = img_str[:-1]

			tweetDict['image'] = img_str
			tweetDict['created_time'] = tweet.timestamp_epochs
			tweetDict['caption'] = tweet.text
			tweetDict['time_scraped'] = datetime.datetime.now()
			tweetDict['session_start'] = self.session_start
			media.append(tweetDict)
		if len(media) > 0: 
			self.latest_timestamp = media[0]['created_time']
		epochDiff = datetime.datetime.now().timestamp() - self.latest_timestamp
		print("Newest post:", "{:.1f}".format(epochDiff/60), "minutes ago")
		return media


	def printKeys(self, dict):
		for key, value in dict.items():
			print(key)


class InstaTagWatcher(TargetWatcher):
	def __init__(self, target, stories=False):
		TargetWatcher.__init__(self,target)
		self.stories=stories
		self.targetString = "instagram:hashtag:" + target

	def scrapeTarget(self, apis):
		instascraper = apis['instagram']
		response = instascraper.tag_feed(self.target, count=10)
		posts = self.convertInstagramResponse(response['data']['hashtag']['edge_hashtag_to_media']['edges'])
		return posts

	
class InstaLocationWatcher(TargetWatcher):
	def __init__(self, target, stories=False):
		TargetWatcher.__init__(self,target)
		self.stories = stories
		self.targetString = "instagram:location:" + target


	def scrapeTarget(self, apis):
		instascraper = apis['instagram']
		response = apis.location_feed(self.target, count=10)
		posts = self.convertInstagramResponse(response['data']['location']['edge_location_to_media']['edges'])
		return posts

class TwitterKeywordWatcher(TargetWatcher):
	def __init__(self, target):
		TargetWatcher.__init__(self,target)
		self.targetString = "twitter:query:" + target

	def scrapeTarget(self, apis):
		twitterscraper = apis['twitter']
		start_date = datetime.date.today()
		end_date = datetime.date.today() + datetime.timedelta(days=1)
		listTweets = twitterscraper.query_tweets(self.target, 40, begindate=start_date, enddate=end_date)
		tweets = self.convertTwitterResponse(listTweets)
		return tweets
