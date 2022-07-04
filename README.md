# Twifesh
After some frustrations with tweepy around the v2 of Twitter API, I decided to write TwiFesh to stream tweets and write them to a json file. <br>
<br> This is initially just going to stream tweets and write them as json to disk. In subsequent modules, we will add other twitter utility and also add funcitonality to upload contents to AWS S3.

**Requirements** 
<br>
- To run this module, some built-in python modules are required
- *requests*
- *datetime from datetime as dt*
<br><br>

- In your elevated dev account, make sure to setup a project in your account and then create an app under the project. It is a requirement from Twitter
- You will then get your bearer token.

- Twitter Docs:
https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/introduction
<br>

**Output**
- The output is a json file with same name as the keywords, ending in the date and time of the run

**Example1**

*twifesh = Twifesh(['a topic', 'another topic'])* <br>
*twifesh.stream_now()*

**Example2**

*twifesh = Twifesh()* <br>
*twifesh.stream_now()*

<br>
- output: *a_topic_another_topic_2022July4_00_00_00s.json*

