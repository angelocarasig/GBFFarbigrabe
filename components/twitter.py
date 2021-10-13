import tweepy

# ----------------------------------------------------------------------------------------------------------------
# Twitter Component
# ----------------------------------------------------------------------------------------------------------------
# Improve the bot features using Twitter
# Tokens must be set in config.json
# ----------------------------------------------------------------------------------------------------------------

class Twitter():
    def __init__(self, bot):
        self.bot = bot
        self.data = None
        self.client = None

    def init(self):
        self.data = self.bot.data
        self.login()

    """login()
    Login to Twitter
    
    Returns
    --------
    bool: True if success, False if not
    """
    def login(self):
        try:
            self.client = tweepy.Client(bearer_token="AAAAAAAAAAAAAAAAAAAAAB9eUgEAAAAAaerPL8%2FiHVZD968zWSWO%2FBUquvQ%3DS3VIPkauDuMnkVFeqlDGusZ3KvfCB8CK0mYCR4JPD2TbDwLzk6")
            self.client.get_user(username='granblue_en', user_fields=['description', 'profile_image_url', 'pinned_tweet_id'])
            return True
        except:
            self.client = None # disable if error
            return False

    """user()
    Return a Twitter user
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user if not
    """
    def user(self, screen_name : str):
        try: return self.client.get_user(username=screen_name, user_fields=['description', 'profile_image_url', 'pinned_tweet_id'])
        except: return None

    """timeline()
    Return a Twitter user timeline
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user timeline if not
    """
    def timeline(self, screen_name, token=None):
        try: 
            user = self.user(screen_name)
            if token is None:
                return self.client.get_users_tweets(id=user.data.id, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id,' 'referenced_tweets.id.author_id'], max_results=10)
            else:
                return self.client.get_users_tweets(id=user.data.id, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id,' 'referenced_tweets.id.author_id'], pagination_token=token, max_results=10)
        except:
            return None

    """pinned()
    Return a Twitter user's pinned tweet.
    Note: it's mostly to access the tweet text. If you are interested in attachments and such, you better use user() and tweet() on your own.
    
    Parameters
    ----------
    screen_name: Twitter user screen name
    
    Returns
    --------
    unknwon: None if error or the user's pinned tweet
    """
    def pinned(self, screen_name):
        try: 
            user = self.user(screen_name)
            tweets = self.tweet([user.data.pinned_tweet_id])
            return tweets.data[0]
        except:
            return None

    """tweet()
    Return a list of tweets
    
    Parameters
    ----------
    ids: List of tweet ids to retrieve
    
    Returns
    --------
    unknwon: None if error or the tweet list dict otherwise
    """
    def tweet(self, ids):
        try: 
            return self.client.get_tweets(ids=ids, tweet_fields=['context_annotations', 'created_at', 'entities', 'public_metrics'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id,' 'referenced_tweets.id.author_id'])
        except:
            return None