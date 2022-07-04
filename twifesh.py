# -*- coding: utf-8 -*-
"""
Created on Sunday July 3, 2022 19:53:37 2018

@author: Fesh
"""
#####################################################################################################################################################################
##Summary: This module streams tweet from the official Twitter API v2 via an elevated developer account.
#Requirements: Modules needed: requests, datetime from datetime brought into the namespace as dt, json, and the user's Twitter dev account bearer_token from keys.py 
#
#After initializing twifesh as a TwiFesh class, call the stream_now method and supply the keywords.
#A json file named after the keyword(s) submitted + time of stream start is saved to the current path of the script.
##Script will run till an error is encountered in the stream or it is stopped with "Ctrl+C" twice.
##############################################################################################################################

import requests
import json
from datetime import datetime as dt
from keys import bearer_token

headers = {"Authorization":f"Bearer {bearer_token}", "User-Agent" : "TwifeshStreamPython"}


class Twifesh():
    def __init__(self):
        self.keywords = [] #This will form part of our filename
        self.time_obj_str = dt.strftime(dt.now(), '%Y%B%d_%H_%M_%ms') #This will form part of our filename
        
    def bearer_oauth(self, r):
        """
        Method required by bearer token authentication.
        """
        r.headers["Authorization"] = f"Bearer {bearer_token}"
        r.headers["User-Agent"] = "TwiFeshStreamer"
        return r


    def get_rules(self):
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream/rules", auth=self.bearer_oauth
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
            )
        try:
            print(f"Last keyword(s) streamed are: => {[line['value'] for line in response.json()['data']][::-1]}")
        except KeyError:
            print(f"The last streaming attempt failed. No keywords in play before now.")
        return response.json()


    def delete_all_rules(self, rules):
        """
        This will take rules arg, a json result from get_rules()
        - If this is None, we return same, otherwise we clear the standing rules
        """
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            auth=self.bearer_oauth,
            json=payload
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot delete rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        print('Old rule(s) successfully cleared!')


    def set_rules(self, delete):
        """
        This uses feedback from the user to get and set the new rule(s)
        """
        print("What are we streaming for? If there are more than one topic, seperate them with commas.\n\
        PS: Maximum topics we are going to take is 5.\n")
        my_rules = input(">>> ")
        while not my_rules:
            print("Please enter a keyword to stream...")
            my_rules = input(">>> ")
        
        keywords = []
        for word in my_rules.split(',')[:5]:
            keeper_dict = {"value": word.strip()}
            keywords.append(keeper_dict)
            self.keywords.append(word.strip())
        
        payload = {"add": keywords}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            auth=self.bearer_oauth,
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(
                "Failed to add rule(s) (HTTP {}): {}".format(response.status_code, response.text)
            )

        print(f"Rule(s) successfully set for keywords {[line for line in self.keywords][:5]}.")
        return True


    def get_stream(self):
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", auth=self.bearer_oauth, stream=True,
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        print("Connection to stream successful!")
        for response_line in response.iter_lines():
            if response_line:
                json_response = json.loads(response_line)
                tweet_id = json_response['data']['id']
                
                #fetch the full tweet details
                try:
                    a_tweet = requests.get(
                        f"https://api.twitter.com/2/tweets/", 
                        params=
                        {'ids':tweet_id, 
                         'user.fields':'created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld',
                         'place.fields':'contained_within,country,country_code,full_name,geo,id,name,place_type', 
                         'tweet.fields':'source,created_at,geo',
                         'expansions': 'referenced_tweets.id.author_id'}, auth=self.bearer_oauth
                        )
                    data = json.loads(a_tweet.text)['data'][0]
                    includes = json.loads(a_tweet.text)['includes']['users'][0]
                    
                    payloader = {
                                    'tweet_id' : data.get('id'),
                                    'created_at' : data.get('created_at'),
                                    'tweet_author_id' : data.get('author_id'),
                                    'tweet_author_description' : includes.get('description'),
                                    'tweet_author_username' : includes.get('username'),
                                    'tweet_author_location' : includes.get('location'),
                                    'tweet_author_image' : includes.get('profile_image_url'),
                                    'tweet_author_join_date': includes.get('created_at'),
                                    'tweet_author_following_count': includes.get('public_metrics').get('following_count'),
                                    'tweet_author_followers_count': includes.get('public_metrics').get('followers_count'),
                                    'tweet_author_total_tweets':includes.get('public_metrics').get('tweet_count'),
                                    'tweet_author_verified': includes.get('public_metrics').get('verified'),
                                    'tweet_author_name': includes.get('public_metrics').get('name'),
                                    'tweet' : data.get('text'),
                                    'source' : data.get('source'),
                                    'quoted_id' : ','.join([line['id'] for line in data.get('referenced_tweets') if line['type'] == 'quoted']),
                                    'in_reply_to_id': ','.join([line['id'] for line in data.get('referenced_tweets') if line['type'] == 'replied_to'])
                                }
                    
                    with open('_'.join(self.keywords) +self.time_obj_str + ".json", "a") as file:
                        data = json.dumps(payloader)
                        file.write(data + '\n')
                    
                    print(data, '\n')
                    
                except Exception as e:
                    print(f"Error fetching full tweet details: => {e}")


    def stream_now(self):
        rules = self.get_rules()
        delete = self.delete_all_rules(rules)
        result = self.set_rules(delete)
        if result:
            self.get_stream()


twifesh = Twifesh()
twifesh.stream_now()