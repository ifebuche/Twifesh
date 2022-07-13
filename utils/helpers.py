from enum import Enum


class BadRequest(Exception):
    """
    handles Exceptions Bad https response 
    """
    ...


class RulesException(Exception):
    """
    handles Exceptions for when rules
    """
    ...


class StreamException(Exception):
    """
    handles Exceptions for  Streams
    """
    ...


class Url(Enum):
    """ Handling Static urls """
    
    tweets = "https://api.twitter.com/2/tweets/"
    user= "https://api.twitter.com/2/users"
    profile = f"{user}/by"
    rules= "https://api.twitter.com/2/tweets/search/stream/rules"
    stream = "https://api.twitter.com/2/tweets/search/stream"
