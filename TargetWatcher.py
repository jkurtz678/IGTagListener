#from instagram_private_api.instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError
import reprlib
import code
import datetime
from bs4 import BeautifulSoup


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

	def convertTwitterResponse(self, timeline):
		media = []
		for tweet in timeline:
			if float(tweet.select('._timestamp')[0]['data-time']) > self.latest_timestamp:
				tweetDict = {}
				#name = tweet.select('.fullname')[0].text
				try:
					tweetDict['id'] = tweet['data-item-id']
					tweetDict['username'] = tweet.select('.username')[0].text
					tweetDict['user_id'] = tweet.select('.js-user-profile-link')[0]['data-user-id']
					tweetDict['caption'] = tweet.select('.tweet-text')[0].text
					tweetDict['created_time'] = tweet.select('._timestamp')[0]['data-time']
					tweetDict['link'] = "https://twitter.com" + tweet.select('.original-tweet')[0]['data-permalink-path']
					tweetDict['query'] = self.targetString
					tweetDict['time_scraped'] = datetime.datetime.now()
					tweetDict['session_start'] = self.session_start
					tweetDict['image'] = ""
					media.append(tweetDict)
				except Exception as e:
					print("Error scraping tweet!", e)
		if len(media) > 0: 
			print("first link:", media[0]['link'])
			self.latest_timestamp = float(media[0]['created_time'])
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
		first_url = 'https://twitter.com/search?f=tweets&vertical=default&q='
		mid_url = self.target.replace(' ', '%20')
		last_url = '&src=typd'
		url = first_url + mid_url + last_url
		print("url:", url)
		twitterscraper = apis['twitter']
		twitterscraper.get(url)
		source = twitterscraper.page_source
		soup = BeautifulSoup(source, 'html.parser')
		timeline = soup.select('#timeline li.stream-item')
		tweets = self.convertTwitterResponse(timeline)
		return tweets
