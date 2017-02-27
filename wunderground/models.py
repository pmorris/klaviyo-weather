from __future__ import unicode_literals
from urllib import request
import json

class ApiClient:

    api_key = '37883be45f3f1a09'

    # icons -- see https://www.wunderground.com/weather/api/d/docs?d=resources/icon-sets&MR=1
    icon_url = 'https://icons.wxug.com/i/c/{icon_set}/{icon_name}.gif'
    icon_set_keys = 'abcdefghijk'
    default_icon_set = 10

    def __init__(self):
        self.api_key = __class__.api_key
        self.request_url = self.__class__.request_url

    def make_request(self, url):
        response = request.urlopen(url)

        # anything other than a 200 response throws an exception
        if response.status != 200:
            raise Exception()

        # parse the json response and return as an object
        return json.loads(response.read().decode())

    @staticmethod
    def get_icon_url(icon, set = default_icon_set):
        icon_set_keys = __class__.icon_set_keys

        if 0 < set <= len(icon_set_keys):
            icon_set = icon_set_keys[set-1]
        else:
            icon_set = icon_set_keys[__class__.default_icon_set - 1]

        return __class__.icon_url.format(icon_name=icon, icon_set=icon_set)


class ApiClientRequestException(Exception):
    """
    Exception raised from unsuccessful HTTP requests

    Attributes:
        url -- the original url requested
        response -- the response from the HTTP request
    """

    def __init__(self, url, response):
        self.url = url
        self.response = response


class Almanac(ApiClient):

    request_url = 'http://api.wunderground.com/api/{api_key}/almanac/q/{state}/{city}.json'

    @staticmethod
    def getRequestUrl(city, state):
        return __class__.request_url.format(
            api_key=ApiClient.api_key,
            city=city.replace(' ', '_').title(),
            state=state.upper()
        )

    def get(self, city, state):
        url = self.getRequestUrl(city, state)
        response = self.make_request(url)
        return response['almanac']


class Conditions(ApiClient):

    request_url = 'http://api.wunderground.com/api/{api_key}/conditions/q/{state}/{city}.json'

    @staticmethod
    def getRequestUrl(city, state):
        return __class__.request_url.format(
            api_key=ApiClient.api_key,
            city=city.replace(' ', '_').title(),
            state=state.upper()
        )

    def get(self, city, state):
        url = self.getRequestUrl(city, state)
        response = self.make_request(url)
        return response['current_observation']


class Forecast(ApiClient):

    request_url = 'http://api.wunderground.com/api/{api_key}/forecast/q/{state}/{city}.json'

    @staticmethod
    def get_request_url(city, state):
        return __class__.request_url.format(
            api_key=ApiClient.api_key,
            city=city.replace(' ', '_').title(),
            state=state.upper()
        )

    def get(self, city, state):
        url = self.get_request_url(city, state)
        response = self.make_request(url)
        return response['forecast']
