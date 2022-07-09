# -*- coding: utf-8 -*-
"""
Created on Sunday July 3, 2022 19:53:37 2022
Updated to initialize with bear_token

@author: Fesh
Contributors: Prince Analyst 
"""
#####################################################################################################################################################################
##Summary: This module streams tweet from the official Twitter API v2 via an elevated developer account.
#Requirements: Modules needed: requests, datetime from datetime brought into the namespace as dt, json, and the user's Twitter dev account bearer_token from keys.py 
#
#After initializing twifesh as a TwiFesh class, call the stream_now method and supply the keywords.
#A json file named after the keyword(s) submitted + time of stream start is saved to the current path of the script.
##Script will run till an error is encountered in the stream or it is stopped with "Ctrl+C" twice.
##############################################################################################################################

import requests, json, re, time
from datetime import datetime as dt

class FeshBuilder:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        self.time_obj_str = dt.strftime(dt.now(), '%Y%B%d_%H_%M_%ms') #This will form part of our filename

    def bearer_oauth(self, header):
        """
        Method required by bearer token authentication.
        """
        header.headers["Authorization"] = f"Bearer {self.bearer_token}"
        header.headers["User-Agent"] = "TwiFeshStreamer"
        return header

    def clean_tweet(self, tweet):
        tweet = re.sub(r"http\S+", "", tweet)
        tweet = re.sub(r"https\S+", "", tweet)
        tweet = re.sub('[^A-Za-z0-9]+', ' ', tweet)
        return tweet

    def get_tweet_details(self, tweet_id):
        """
        Get the full detail of a tweet by tweet id string
        """
        try:
            a_tweet = requests.get(
                f"https://api.twitter.com/2/tweets/", 
                params=
                {   'ids':tweet_id, 
                    'user.fields':'created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld',
                    'place.fields':'contained_within,country,country_code,full_name,geo,id,name,place_type', 
                    'tweet.fields':'source,created_at,geo',
                    'expansions': 'referenced_tweets.id.author_id'}, auth=self.bearer_oauth
                )
            if a_tweet.status_code != 200:
                json_response = json.loads(a_tweet.text)
                status = json_response.get('status')
                if status and status == 429:
                    print(f"Erm... We have hit Twitter rate limit. Sleeping for 15 minutes are recommended before we continue.\nIf you do not want to wait, please hit with Ctrl + C twice.")
                    time.sleep((60*60)*16)    
                    # raise SystemExit
            data = json.loads(a_tweet.text)['data'][0]
            includes = json.loads(a_tweet.text)['includes']['users'][0]
            #print(f"data => {data}\nincludes => {includes}")
            
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
                            'cleaned_tweet' : self.clean_tweet(data.get('text')),
                            'source' : data.get('source'),
                            'quoted_id': None,
                            'in_reply_to_id': None
                        }
            if data.get('referenced_tweets'):
                try:
                    payloader['quoted_id'] = ','.join([line['id'] for line in data.get('referenced_tweets') if line['type'] == 'quoted'])
                except:
                    pass
                try:
                    payloader['in_reply_to_id'] = ','.join([line['id'] for line in data.get('referenced_tweets') if line['type'] == 'replied_to'])
                except:
                    pass
            return payloader            
        except Exception as e:

            print(f"Error fetching full tweet details: => {e}")

class Profile(FeshBuilder):
    def __init__(self, bearer_token, usernames):
        """
        username: string with profile names seperated by commas and no spaces. eg: "profile1,profile2"
        """
        super().__init__(bearer_token)
        self.usernames = usernames


    def get_profile(self):
        params = {
            "user.fields":"description,created_at,pinned_tweet_id,location,verified,profile_image_url,public_metrics",
            "usernames": self.usernames}
        url = "https://api.twitter.com/2/users/by"
        
        try:
            response = requests.request("GET", url, auth=self.bearer_oauth, params=params)
            if response.status_code != 200:
                raise Exception(f"Request returned an error: {response.status_code} { response.text}")
            json_response = response.json()
            result = []
            try:
                #Success with profile(s) match found
                data = json_response.get('data')
                errors = json_response.get('errors')
                if data:
                    for item in data:
                        result.append(item)
                if errors:
                    for item in errors:
                        result.append(item['detail'])
            except KeyError:
                #Success with no profile(s) match found
                data =  json_response['errors']
                if data:
                    for item in data:
                        result.append(item['detail'])
            return result
        except Exception as e:
            print(f"Error fetching profile(s) url: {e}")
            return None
        

class Profiler(FeshBuilder):
    """
    Get all the tweets from a tweeter user
    """
    def __init__(self, bearer_token, usernames):
        """
        username: string with profile names seperated by commas and no spaces. eg: "profile1,profile2"
        """
        super().__init__(bearer_token)
        self.usernames = usernames

    def get_profile_id(self):
        twifesh=Profile(self.bearer_token, self.usernames)
        speaker = twifesh.get_profile()
        if speaker:
            try:
                user_id = speaker[0].get('id')
                if user_id:
                    return user_id
            except AttributeError:
                if 'Could not find user with usernames' in speaker[0]:
                    return None
        return None

    def _mini_clean(self, data):
        this_page_of_tweets = []
        for tweet in data:
            public_metrics = tweet.get('public_metrics')
            del tweet['public_metrics']
            tweet['retweet_count'] = public_metrics.get('retweet_count', 'no data')
            tweet['reply_count'] = public_metrics.get('reply_count', 'no data')
            tweet['like_count'] = public_metrics.get('like_count', 'no data')
            tweet['quote_count'] = public_metrics.get('quote_count', 'no data')
            this_page_of_tweets.append(tweet)
        return this_page_of_tweets

    def get_profile_tweets(self):
        """
        Get first page of response
        """
        user_id = self.get_profile_id()
        if not user_id:
            print(f"We could not find a Twitter user with the username: '{self.usernames}'")
            return None
        tweets = []
        page = 1
        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {"tweet.fields": "created_at,public_metrics", "max_results":100}
        
        response = requests.request("GET", url, auth=self.bearer_oauth, params=params)
        if response.status_code != 200:
            raise Exception(f"Request returned an error: {response.status_code} {response.text}")
        
        json_response = response.json()
        data = json_response.get('data')
        if data:
            mini_cleaned = self._mini_clean(data)
            tweets.extend(mini_cleaned)
        next_page = json_response.get('meta').get('next_token')
        while next_page:
            print(f'page {page}')
            page += 1
            params['pagination_token'] = next_page
            response = requests.request("GET", url, auth=self.bearer_oauth, params=params)
            json_response = response.json()
            data = json_response.get('data')
            if data:
                mini_cleaned = self._mini_clean(data)
                tweets.extend(mini_cleaned)
            next_page = json_response.get('meta').get('next_token')
        
        return tweets



class Stream(FeshBuilder):
    def __init__(self, bearer_token, keywords=None, full_details=False, write_file=False):
        super().__init__(bearer_token)
        self.write_file = False
        if write_file:
            self.write_file = write_file
        self.keywords = keywords
        if not self.keywords:
            self.keywords = []
        self.full_details = full_details

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
        keywords_array = []

        if not self.keywords:
            attempts = 0
            print("What are we streaming for? If there are more than one topic, seperate them with commas.\n\
            PS: Maximum topics we can stream is 5.\n")
            my_rules = input(">>> ")
            while not my_rules:
                if attempts == 3:
                    print("Please restart the module.")
                    raise SystemExit
                attempts += 1
                print(f"We need a keyword or an array of keywords, max 5. Please try again: {attempts}/3")
                print("Please enter a keyword to stream...")
                my_rules = input(">>> ")
            
            
            for word in my_rules.split(',')[:5]:
                keeper_dict = {"value": word.strip()}
                keywords_array.append(keeper_dict)
                self.keywords.append(word.strip())
        else:
            for word in self.keywords:
                keeper_dict = {"value": word.strip()}
                keywords_array.append(keeper_dict) 
        
        payload = {"add": keywords_array}
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
        print("Connection to stream successful! \nListening ...")
        for response_line in response.iter_lines():
            if response_line:
                tweet_details = json.loads(response_line)
                if self.full_details:
                    #fetch the full tweet details
                    tweet_id = tweet_details['data']['id']
                    tweet_details = self.get_tweet_details(tweet_id)
            if self.write_file:
                if tweet_details:
                    with open('_'.join(self.keywords) +self.time_obj_str + ".json", "a") as file:
                        data = json.dumps(tweet_details)
                        file.write(data + '\n')
            print(tweet_details, '\n')                   
                

    def stream_now(self):
        rules = self.get_rules()
        delete = self.delete_all_rules(rules)
        result = self.set_rules(delete)
        if result:
            self.get_stream()