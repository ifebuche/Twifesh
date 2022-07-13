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
from collections import deque
from utils.helpers import (BadRequest, RulesException, StreamException, Url)

class FeshBuilder:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        self.time_obj_str = dt.strftime(dt.now(), '%Y%B%d_%H_%M_%ms') #This will form part of our filename

    def bearer_oauth(self, header):
        """
        Method required by bearer token authentication.
        """
        header.headers["Authorization"] = f"Bearer {self.bearer_token}"
        header.headers["User-Agent"] = "TwiFeshStreamerTitterAPIv2"
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
                Url.tweets.value, 
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
                    return False, f"{status}: rate limit reached"
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
            return True, payloader            
        except Exception as e:
            message = f"error fetching full tweet details: => {e}"
            return False, message

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
        url = Url.profile.value
        
        try:
            response = requests.request("GET", url, auth=self.bearer_oauth, params=params)
            if response.status_code != 200:
                raise BadRequest(f"Request returned an error: {response.status_code} { response.text}")
            json_response = response.json()
            result = deque() #optimized for collection of data. works like list but faster
            try:
                #Success with profile(s) match found
                data = json_response.get('data')
                errors = json_response.get('errors')
                if data:

                    result.extend(data)
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
    def __init__(self, bearer_token, username):
        """
        username: string with the profile name/handle
        """
        super().__init__(bearer_token)
        self.usernames = username

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

    def _mini_clean(self, data, profiles=False, tweets=False):
        this_page = deque()
        for line in data:
            public_metrics = line.get('public_metrics')
            del line['public_metrics']
            if tweets:
                line['retweet_count'] = public_metrics.get('retweet_count', 'no data')
                line['reply_count'] = public_metrics.get('reply_count', 'no data')
                line['like_count'] = public_metrics.get('like_count', 'no data')
                line['quote_count'] = public_metrics.get('quote_count', 'no data')
            elif profiles:
                line['followers_count'] = public_metrics.get('followers_count', 'no data')
                line['following_count'] = public_metrics.get('following_count', 'no data')
                line['tweet_count'] = public_metrics.get('tweet_count', 'no data')
                line['listed_count'] = public_metrics.get('listed_count', 'no data')
            this_page.append(line)
        return this_page

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
        url = f"{Url.user.value}/{user_id}/tweets"
        params = {"tweet.fields": "created_at,public_metrics", "max_results":100}
        
        response = requests.request("GET", url, auth=self.bearer_oauth, params=params)
        if response.status_code != 200:
            raise BadRequest(f"Request returned an error: {response.status_code} {response.text}")
        
        json_response = response.json()
        data = json_response.get('data')
        if data:
            mini_cleaned = self._mini_clean(data, tweets=True)
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
                mini_cleaned = self._mini_clean(data, tweets=True)
                tweets.extend(mini_cleaned)
            next_page = json_response.get('meta').get('next_token')
        
        return tweets

    def get_followers_following(self, pages=1, target='followers'):
        """
        Get the followers of a user/profileby username/handle or who they are following
        - user_id of user to find their followers
        - pages will take a maximum of 20: each page is 250 results. 1k max retrievals to stay within bounds(?)
        """
        if pages > 20:
            pages = 20
        user_id = self.get_profile_id()
        if not user_id:
            print(f"We could not find a Twitter user with the username: '{self.usernames}'")
            return None

        url = f"https://api.twitter.com/2/users/{user_id}/followers"
        if target.lower().strip() == 'following':
            url = f"https://api.twitter.com/2/users/{user_id}/following"

        params = {'user.fields':'created_at,public_metrics,location,verified', 'max_results':250}
        page = 1
        response = requests.get(url, auth=self.bearer_oauth, params=params)
        json_response =  json.loads(response.text)
        user_data = json_response['data']
        followers = []
        
        if user_data:
            mini_cleaned = self._mini_clean(user_data, profiles=True)
            followers.extend(mini_cleaned)
            print(f"page {page}")
            next_page = json_response.get('meta').get('next_token')
            while next_page:
                if page == pages: #stop at the end of the requested number of pages. Max will be 20
                    break
                page += 1
                params['pagination_token'] = next_page
                response = requests.get(url, auth=self.bearer_oauth, params=params)
                json_response = response.json()
                user_data = json_response.get('data')
                if user_data:
                    mini_cleaned = self._mini_clean(user_data, profiles=True)
                    followers.extend(mini_cleaned)
                    print(f'page {page}')
                next_page = json_response.get('meta').get('next_token')
                
        return followers



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
        self.attempts = 1
        self.expo_time = 2
        self.broken = False

    def get_rules(self):
        response = requests.get(
            Url.rules.value, auth=self.bearer_oauth
        )
        if response.status_code != 200:
            raise RulesException("Cannot get rules (HTTP {response.status_code}): {response.text}")

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
            Url.rules.value,
            auth=self.bearer_oauth,
            json=payload
        )
        if response.status_code != 200:
            raise RulesException("Cannot delete rules (HTTP {response.status_code}): {response.text}")

        print('Old rule(s) successfully cleared!')
        return True


    def set_rules(self):
        """
        This uses feedback from the user to get and set the new rule(s)
        """
        keywords_array = deque()

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
            Url.rules.value ,
            auth=self.bearer_oauth,
            json=payload,
        )
        if response.status_code != 201:
            raise RulesException("Cannot add rules (HTTP {response.status_code}): {response.text}")

        print(f"Rule(s) successfully set for keywords {[line for line in self.keywords][:5]}.")
        return True

    def get_stream(self):
        repetition_breaker = None #Twitter will return same tweet if rate limit is reached but app is restarted. If this is value is same as last tweet, treat is as limit reached and sleep 15
        
        response = requests.get(Url.stream.value , auth=self.bearer_oauth, stream=True)
        if response.status_code != 200:
            raise StreamException(f"Cannot get stream (HTTP {response.status_code}): {response.text}")
        print(f"Connection to stream successful! status: {response.status_code} \nListening ...")

        for response_line in response.iter_lines():
            if response_line:
                #Reset exponential timer and attemps count in case they have been used at a stream drop
                if self.attempts > 1:
                    self.attempts = 1
                if self.expo_time > 2:
                    self.expo_time = 2
                    
                tweet_details = json.loads(response_line)
                if self.full_details:
                    #fetch the full tweet details
                    tweet_id = tweet_details['data']['id']
                    status, tweet_details = self.get_tweet_details(tweet_id)
                    if self.write_file:
                        if tweet_details:
                            if 'rate limit reached' not in tweet_details:
                                with open('_'.join(self.keywords) +self.time_obj_str + ".json", "a") as file:
                                    data = json.dumps(tweet_details)
                                    file.write(data + '\n')
                    #Check for repeat tweets.
                    if status:
                        print(tweet_details, '\n')
                        if repetition_breaker == tweet_details:
                            print(f"Same exact tweet returned. We suspect a possinble limit issue.\nResetting connection to the stream after 60 seconds...")
                            response.close()
                            print(f"Sleep started @ {dt.now().time()}\n")
                            time.sleep(60*1)
                            if self.attempts < 5:
                                self.attempts = 1
                                self.get_stream()
                            else:
                                print(f"We could not restablish the stream after {self.attempts} trials.")
                                raise SystemExit
                        self.attempts = 1
                        repetition_breaker = tweet_details
                    else:
                        if 'rate limit reached' in tweet_details:
                            print(f"{tweet_details}\nWe will sleep for 15 minutes.")
                            print(f"Sleep started @ {dt.now().time()}")
                            time.sleep(60*16)
                        elif tweet_details.startswith('error'):
                            print(tweet_details)

                else:
                    continue #No tweet was recieved for the tweet_id. Ignore
            else:
                response.close()
                print(f"We received an empty byte data: Stream disconnected.\nStarting exponential back-off.\nSleep started @ {dt.now()}")
                print(f"Sleep: {self.expo_time} seconds ...\n")
                time.sleep(self.expo_time)
                self.expo_time *= 2
                self.attempts += 1
                if self.expo_time < 60*10:
                    try:
                        self.get_stream()
                    except Exception as e: #Possible ConnectionAbortedError
                        print(f"An uncaught error occurred: {e}")
                        raise SystemExit
                else:
                    print(f"We could not reconnect the stream after {self.attempts} attempts in the past 10 minutes.\n.Exiting...")
                        
    def stream_now(self):
        """
        - Initiate steps to stream.
        """
        rules = self.get_rules()
        deleted = self.delete_all_rules(rules)
        if deleted: 
            result = self.set_rules()
            if result:
                self.get_stream()