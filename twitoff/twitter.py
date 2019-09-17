""" Retrieve Tweets, embeddings, and persist in the Database """

import tweepy, basilica
from decouple import config
from .models import DB, Tweet, User

TWITTER_AUTH = tweepy.OAuthHandler(config('TWITTER_CONSUMER_KEY'),
                                   config('TWITTER_CONSUMER_SECRET'))
TWITTER_AUTH.set_access_token(config('TWITTER_ACCESS_TOKEN'),
                              config('TWITTER_ACCESS_TOKEN_SECRET'))
TWITTER = tweepy.API(TWITTER_AUTH)

BASILICA = basilica.Connection(config('BASILICA_KEY'))


# TODO write some useful functions 

def add_or_update_user(username):
    """ add or update a user *and* their tweets, error if no/private user.""""
    """ If not private and no error, will pass to the else statement that commits the data  """"
    try:
        twitter_user = TWITTER.get_user(username)
        db_user = (User.query.get(twitter_user.id) or 
                   User(id=twitter_user.id, name=username))
        DB.session.add(db_user)      
        # We want as many recent nonretweet/reply statuses as we can get     
        tweets = twitter_user.timeline(
            count=200, exlude_replies=True, include_rts=False,
            tweet_mode='extended', since_id=db_user.newest_tweet_id)
        if tweets:
            db_user.newest_tweet_id = tweets[0].id
        for tweet in tweets:
            # Get embedding for tweet, and store in db
            embedding = BASILICA.embed_sentence(tweet.full_text,
                                                model='twitter')
            db_tweet = Tweet(id=tweet.id, text=tweet.full_text[:500],
                             embedding=embedding)
            db_user.tweets.append(db_tweet)
            DB.session.add(db_tweet)                                          
    except Exception as e:
        print('Error Processing {} : {}'.format(username, e))
        raise e
    else:
        # if no errors then commit to database
        DB.session.commit()