from sploitkit import *
import requests
import json
from terminaltables import SingleTable
import twint
from datetime import datetime

class twitterFollowerSearch(Module):
    """ This module find twitter account
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'USERNAME',
            "Provide your target Username",
            True,
        ): str("laet4x"),
    })    

    def run(self):
        today = datetime.now().strftime('%Y-%m-%d')
        c = twint.Config()
        username = self.config.option('USERNAME').value
        c.To = username
        c.Since = today
        c.Followers = True
        c.Hide_output = True
        c.Store_object = True

        twint.run.Search(c)

        tweets = twint.output.tweets_list

        followers = []

        for tweet in tweets:
                followers.append(('{}'.format(tweet.username)))

        print(followers)


