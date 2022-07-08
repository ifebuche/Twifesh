# Twifesh
After some frustrations with tweepy around the v2 of Twitter API, I decided to write TwiFesh to stream tweets and write them to a json file. <br>
<br> This is initially just going to stream tweets and write them as json to disk. In subsequent modules, we will add other twitter utility and also add funcitonality to upload contents to AWS S3.
<br><br>

## Updates
- More refactoring
- Added support for Twitter user Profile retrieval with the twifesh.api.Profile class

**Requirements** 
<br>
- This module runs with builtin modules up to version 0.0.2
<br>

- In your elevated dev account, make sure to setup a project in your account and then create an app under the project. It is a requirement from Twitter
- You will then get your bearer token.

- Twitter Docs:
https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction
<br>

**Output**
- The output is a json file with same name as the keywords, ending in the date and time of the run

**Example1: file written, no interraction**

$ from twifesh.api import Stream <br>
$ twifesh = Stream(bearer_token, keywords=['topic1', 'topic2'], write_file=True) <br>
$ twifesh.stream_now() <br>

- output: *topic1_topic2_2022July4_00_00_00s.json*
<br><br>

**Example2: no file written, asks for the topic(s)**

$ from twifesh.api import Stream<br>
$ twifesh = Stream(bearer_token) <br>
$ twifesh.stream_now()

<br>