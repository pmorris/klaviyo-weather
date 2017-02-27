from django.test import TestCase

from .models import Almanac, Conditions, Forecast

class ApiClientTest(TestCase):
    def test_init(self):
        a = Almanac()
        expected_url = 'http://api.wunderground.com/api/37883be45f3f1a09/almanac/q/CA/San_Francisco.json'
        actual_url = a.get_request_url('San_Francisco', 'CA')
        self.assertEqual(a.get_request_url('San_Francisco', 'CA'), expected_url)

        self.assertRegex(a.api_key, r'^[0-9a-z]+$')

        # icon url attributes
        self.assertIsInstance(Almanac.icon_url, str)
        self.assertIsInstance(Almanac.icon_set_keys, str)
        self.assertIsInstance(Almanac.default_icon_set, int)

    def test_icon_url_default_set(self):
        expected_url = 'https://icons.wxug.com/i/c/j/partlycloudy.gif'
        self.assertEqual(expected_url, Almanac.get_icon_url('partlycloudy'))

    def test_icon_url_custom_set(self):
        expected_url = 'https://icons.wxug.com/i/c/b/partlycloudy.gif'
        self.assertEqual(expected_url, Almanac.get_icon_url('partlycloudy', 2))

    def test_icon_url_custom_set_out_of_range(self):
        expected_url = 'https://icons.wxug.com/i/c/j/partlycloudy.gif'
        self.assertEqual(expected_url, Almanac.get_icon_url('partlycloudy', 200))


class AlmanacTest(TestCase):
    def test_almanac_url(self):
        expected_url = 'http://api.wunderground.com/api/37883be45f3f1a09/almanac/q/CA/San_Francisco.json'
        self.assertEqual(Almanac.get_request_url('San_Francisco', 'CA'), expected_url)
        self.assertEqual(Almanac.get_request_url('San Francisco', 'ca'), expected_url)

    def test_almanac_response(self):
        client = Almanac()
        response = client.get('San Francisco', 'CA')
        self.assertIsInstance(response, dict)

        # average temperature
        self.assertTrue(response['temp_high']['normal']['F'].isnumeric())


class ConditionsTest(TestCase):
    def test_conditions_url(self):
        expected_url = 'http://api.wunderground.com/api/37883be45f3f1a09/conditions/q/CA/San_Francisco.json'
        self.assertEqual(Conditions.get_request_url('San_Francisco', 'CA'), expected_url)
        self.assertEqual(Conditions.get_request_url('San Francisco', 'ca'), expected_url)

    def test_conditions_response(self):
        client = Conditions()
        response = client.get('San Francisco', 'CA')
        self.assertIsInstance(response, dict)

        # current temperature
        self.assertIsInstance(response['temp_f'], float)

        # current sky conditions
        self.assertGreater(response['weather'], '')


class ForecastTest(TestCase):
    def test_forecast_url(self):
        expected_url = 'http://api.wunderground.com/api/37883be45f3f1a09/forecast/q/CA/San_Francisco.json'
        self.assertEqual(Forecast.get_request_url('San_Francisco', 'CA'), expected_url)
        self.assertEqual(Forecast.get_request_url('san francisco', 'ca'), expected_url)

    def test_forecast_response(self):
        client = Forecast()
        response = client.get('San Francisco', 'CA')
        self.assertIsInstance(response, dict)

        # high temp
        self.assertTrue(response['simpleforecast']['forecastday'][0]['high']['fahrenheit'].isnumeric())
        self.assertGreater(response['simpleforecast']['forecastday'][0]['conditions'], '')
