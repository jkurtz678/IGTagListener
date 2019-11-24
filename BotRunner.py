from IGBot import IGBot
import argparse
from TargetWatcher import InstaTagWatcher, InstaLocationWatcher, TwitterKeywordWatcher

parser = argparse.ArgumentParser()
parser.add_argument("--headless", help="run without client", action="store_true")
args = parser.parse_args()

if(args.headless):
	print("running headless")
else:
	print("running with client")
targets = [InstaTagWatcher('culvercity'), InstaLocationWatcher('213420290'), TwitterKeywordWatcher("culver city")]
bot = IGBot(headless = args.headless)
bot.run(targets)

