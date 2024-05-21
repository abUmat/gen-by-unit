import json
import sys
sys.path.append('./packages')
from packages import tweepy

class TweepyClient:
    def __init__(self, config_file_path: str) -> None:
        config = json.load(open(config_file_path, 'r'))
        self.client = tweepy.Client(config['twitter']['bearerToken'],
                                    config['twitter']['consumerKey'],
                                    config['twitter']['consumerSecret'],
                                    config['twitter']['accessToken'],
                                    config['twitter']['accessTokenSecret']
                                    )
        auth = tweepy.OAuthHandler(config['twitter']['consumerKey'],
                                   config['twitter']['consumerSecret'])
        auth.set_access_token(config['twitter']['accessToken'],
                              config['twitter']['accessTokenSecret'])
        self.api = tweepy.API(auth)
    def tweet(self, text: str, media_paths: list[str]=[], in_reply_to_tweet_id: str='') -> str:
        '''
        1件ツイートしTweetIDを返す
        '''
        if media_paths:
            media = [self.api.media_upload(filename=media_path) for media_path in media_paths]
            if in_reply_to_tweet_id:
                resp = self.client.create_tweet(text=text, media_ids=[m.media_id for m in media], in_reply_to_tweet_id=in_reply_to_tweet_id)
            else:
                resp = self.client.create_tweet(text=text, media_ids=[m.media_id for m in media])
        else:
            if in_reply_to_tweet_id:
                resp = self.client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id)
            else:
                resp = self.client.create_tweet(text=text)
        return resp.data['id']
    def tweet_many(self, text_s: list[str], media_paths_s: list[list[str]]) -> None:
        '''
        連続ツイートする
        '''
        assert(len(text_s) <= 10)
        assert(len(media_paths_s) <= 10)
        # 長さを合わせる
        while len(text_s) < len(media_paths_s):
            text_s.append('')
        while len(media_paths_s) < len(text_s):
            media_paths_s.append([])
        in_reply_to_tweet_id = ''
        for text, media_paths in zip(text_s, media_paths_s):
            in_reply_to_tweet_id = self.tweet(text, media_paths, in_reply_to_tweet_id)
