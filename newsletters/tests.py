from django.test import TestCase
from django.core.exceptions import ValidationError
from django.test import Client
from django.core.urlresolvers import reverse
from django.test.utils import setup_test_environment
from urllib.parse import urlparse, parse_qs

from .models import Subscriber, SubscriberLocation, Weather

class SubscriberLocationTests(TestCase):

    def test_instantiation(self):
        obj = SubscriberLocation(id=999, city='Quahog', state_abv='RI')
        self.assertEquals(obj.id, 999)
        self.assertEquals(obj.city, 'Quahog')
        self.assertEquals(obj.state_abv, 'RI')

    def test_state_name_with_known_abbreviation(self):
        """
        state_name() should return a non-empty string when a valid abbreviation is provided
        :return:
        """

        state_name = SubscriberLocation.state_name('MA')
        self.assertEqual(state_name, 'Massachusetts')

    def test_state_name_with_known_lowercase_abbreviation(self):
        self.assertEqual(SubscriberLocation.state_name('ma'), 'Massachusetts')

    def test_state_name_with_unknown_abbreviation(self):
        self.assertEqual(SubscriberLocation.state_name('foo'), '')

    def test_state_name_with_integer(self):
        self.assertEqual(SubscriberLocation.state_name(123), '')

    def test_state_name_with_list(self):
        self.assertEqual(SubscriberLocation.state_name(['foo']), '')

    def test_state_name_with_dict(self):
        self.assertEqual(SubscriberLocation.state_name({'foo': 'bar'}), '')

class SubscriberTests(TestCase):

    def test_instantiation(self):
        obj = Subscriber(email_address='eat@joes.com', location=SubscriberLocation(), is_subscribed=True)
        self.assertIsInstance(obj, Subscriber)
        self.assertEquals(obj.email_address, 'eat@joes.com')
        self.assertTrue(obj.is_subscribed)

    def test_post_init(self):
        obj = Subscriber(email_address='eat@joes.com', location=SubscriberLocation(), is_subscribed=True)
        self.assertIsInstance(obj, Subscriber)
        self.assertRegex(obj.token, r"[A-z0-9\-]{32}")

    def test_clean(self):
        location = SubscriberLocation.objects.create(id=999, city='Quahog', state_abv='RI')
        obj = Subscriber(email_address='eatjoes.com', location=location, is_subscribed=True)

        # self.assertRaises(ValidationError, obj.clean)
        with self.assertRaisesMessage(ValidationError, 'Invalid Email Address'):
            obj.clean()

    def test_save(self):
        location = SubscriberLocation.objects.create(id=999, city='Quahog', state_abv='RI')
        obj = Subscriber(email_address='eat@joes.com', location=location, is_subscribed=True)
        obj.save()
        self.assertGreater(obj.id, 0)

    def test_save_validation_error(self):
        location = SubscriberLocation.objects.create(id=999, city='Quahog', state_abv='RI')
        obj = Subscriber(email_address='eat', location=location, is_subscribed=True)
        with self.assertRaisesMessage(ValidationError, 'Invalid Email Address'):
            obj.save()

    def test_valid_email(self):
        self.assertTrue(Subscriber.is_valid_email_address('eat@joes.com'))
        self.assertTrue(Subscriber.is_valid_email_address('eat+food@joes.com'))

    def test_invalid_email(self):
        self.assertFalse(Subscriber.is_valid_email_address('eat@joes'))
        self.assertFalse(Subscriber.is_valid_email_address('joes.com'))
        self.assertFalse(Subscriber.is_valid_email_address('eat:joes.com'))
        self.assertFalse(Subscriber.is_valid_email_address('mailto:eat@joes.com'))
        self.assertFalse(Subscriber.is_valid_email_address('http://eat@joes.com'))

class NewsletterViewTests(TestCase):
    fixtures = ['newsletters/fixtures/newsletters.json', ]

    def setUp(self):
        setup_test_environment()
        self.client = Client()

    def test_index_available(self):
        response = self.client.get(reverse('newsletters:index'))
        self.assertEqual(response.status_code, 200)

    def test_index_context_location_group(self):
        response = self.client.get(reverse('newsletters:index'))
        context = response.context
        self.assertIn('location_group', response.context)
        self.assertIsInstance(response.context['location_group'], dict)

        # expect 100 cities
        num_cities = 0
        for state, locations in response.context['location_group'].items():
            num_cities += len(locations)
        self.assertEqual(num_cities, 100)

    def test_subscribe_allowed_methods(self):
        uri = reverse('newsletters:subscribe')
        data = {'email': 'eat@joes.com', 'location': 5}

        # get
        response = self.client.get(uri, data)
        self.assertEqual(response.status_code, 405)

        # put
        response = self.client.put(uri, data)
        self.assertEqual(response.status_code, 405)

        # delete
        response = self.client.delete(uri, data)
        self.assertEqual(response.status_code, 405)

    def test_subscribe_invalid_parameters(self):
        uri = reverse('newsletters:subscribe')
        ruri = reverse('newsletters:index')

        # missing email
        data = {'email': '', 'location': '5'}
        response = self.client.post(uri, data)
        self.assertEqual(response.status_code, 302)
        parsed_url = urlparse(response.url)
        parsed_qs = parse_qs(parsed_url.query, keep_blank_values=True)
        self.assertEqual(urlparse(response.url).path, ruri)
        self.assertEqual(parsed_qs.get('email', [''])[0], data['email'])
        self.assertEqual(parsed_qs.get('loc', [''])[0], data['location'])

        # malformed email
        data = {'email': 'eat@joes', 'location': '5'}
        response = self.client.post(uri, data)
        parsed_url = urlparse(response.url)
        parsed_qs = parse_qs(parsed_url.query, keep_blank_values=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, ruri)
        self.assertEqual(parsed_qs.get('email', [''])[0], data['email'])
        self.assertEqual(parsed_qs.get('loc', [''])[0], data['location'])

        # missing location
        data = {'email': 'eat@joes.com', 'location': ''}
        response = self.client.post(uri, data)
        parsed_url = urlparse(response.url)
        parsed_qs = parse_qs(parsed_url.query, keep_blank_values=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, ruri)
        self.assertEqual(parsed_qs.get('email', [''])[0], data['email'])
        self.assertEqual(parsed_qs.get('loc', [''])[0], data['location'])

        # invalid location
        data = {'email': 'eat@joes.com', 'location': 'abc'}
        response = self.client.post(uri, data)
        parsed_url = urlparse(response.url)
        parsed_qs = parse_qs(parsed_url.query, keep_blank_values=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, ruri)
        self.assertEqual(parsed_qs.get('email', [''])[0], data['email'])
        self.assertEqual(parsed_qs.get('loc', [''])[0], data['location'])

        # unknown location
        data = {'email': 'eat@joes.com', 'location': '9999999'}
        response = self.client.post(uri, data)
        parsed_url = urlparse(response.url)
        parsed_qs = parse_qs(parsed_url.query, keep_blank_values=True)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, ruri)
        self.assertEqual(parsed_qs.get('email', [''])[0], data['email'])
        self.assertEqual(parsed_qs.get('loc', [''])[0], data['location'])

    def test_subscribe_duplicate_email_and_location(self):
        location = SubscriberLocation.objects.first()
        self.assertIsInstance(location, SubscriberLocation)

        subscriber = Subscriber(email_address="eat@joes.com", location=location)
        subscriber.save()

        self.assertEqual(location.id, subscriber.location.id)

        uri = reverse('newsletters:subscribe');
        data =  {"email":subscriber.email_address, "location": subscriber.location.id}
        response = self.client.post(uri, data)
        self.assertEqual(response.status_code, 302)

    def test_subscribe_duplicate_email_with_new_location(self):
        location = SubscriberLocation(city="Quahog", state_abv="RI")
        location.save()

        subscriber = Subscriber(email_address="eat@joes.com", location=location)
        subscriber.save()

        # get random location
        new_location = SubscriberLocation.objects.first()
        self.assertIsInstance(new_location, SubscriberLocation)
        self.assertNotEqual(location.id, new_location.id)

        uri = reverse('newsletters:subscribe');
        data = {"email": subscriber.email_address, "location": new_location.id}
        response = self.client.post(uri, data)
        self.assertEqual(response.status_code, 302)

    def test_subscribe_success(self):
        location = SubscriberLocation.objects.first()
        self.assertIsInstance(location, SubscriberLocation)

        uri = reverse('newsletters:subscribe');
        data = {"email": "eat@joes.com", "location": location.id}
        response = self.client.post(uri, data)
        subscriber = Subscriber.objects.get(email_address=data['email'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.url).path, reverse('newsletters:subscriber', kwargs={'token': subscriber.token}))
        self.assertRegex(response.url, subscriber.token)

    def test_subscriber_detail_404(self):
        response = self.client.get(reverse('newsletters:subscriber', kwargs={'token': 'abcd'}))
        self.assertEqual(response.status_code, 404)

    def test_subscriber_detail(self):
        # create a subscriber
        location = SubscriberLocation.objects.first()
        sub = Subscriber.objects.create(email_address="eat@joes.com", location=location)
        sub.save()

        # verify subscriber creation
        self.assertGreater(sub.id, 0)
        self.assertRegex(sub.token, r"[A-z0-9\-]{32}")
        self.assertIsInstance(sub, Subscriber)
        uri = reverse('newsletters:subscriber', kwargs={'token': sub.token})
        response = self.client.get(uri)

        # inspect response
        self.assertEqual(response.status_code, 200)

        # inspect response.context.subscriber
        self.assertIn('subscriber', response.context)
        self.assertIsInstance(response.context['subscriber'], Subscriber)
        self.assertEquals(response.context['subscriber'].token, sub.token)

    def test_subscriber_opt_out_link(self):
        # create a subscriber
        location = SubscriberLocation.objects.first()
        sub = Subscriber.objects.create(email_address="eat@joes.com", location=location, is_subscribed=True)
        sub.save()

        # verify subscriber creation
        self.assertIsInstance(sub, Subscriber)
        self.assertGreater(sub.id, 0)
        self.assertRegex(sub.token, r"[A-z0-9\-]{32}")
        self.assertTrue(sub.is_subscribed)

        # make http request to subscriber page
        uri = reverse('newsletters:subscriber', kwargs={'token': sub.token})
        response = self.client.get(uri)
        self.assertEquals(response.status_code, 200)

        # make http request to the opt-in-link from the response.context
        self.assertIn('opt_out_uri', response.context)
        self.assertIsInstance(response.context['opt_out_uri'], str)
        uri = response.context['opt_out_uri']
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)

        # verify unsibscribe
        sub2 = Subscriber.objects.get(pk=sub.pk)
        self.assertFalse(sub2.is_subscribed)

    def test_subscriber_opt_in_link(self):
        # create a subscriber
        location = SubscriberLocation.objects.first()
        sub = Subscriber.objects.create(email_address="eat@joes.com", location=location, is_subscribed=False)
        sub.save()

        # verify subscriber creation
        self.assertIsInstance(sub, Subscriber)
        self.assertGreater(sub.id, 0)
        self.assertRegex(sub.token, r"[A-z0-9\-]{32}")
        self.assertFalse(sub.is_subscribed)

        # make http request to subscriber page
        uri = reverse('newsletters:subscriber', kwargs={'token': sub.token})
        response = self.client.get(uri)
        self.assertEquals(response.status_code, 200)

        # make http request to the opt-in-link from the response.context
        self.assertIn('opt_in_uri', response.context)
        self.assertIsInstance(response.context['opt_in_uri'], str)
        uri = response.context['opt_in_uri']
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)

class EmailPreviewTests(TestCase):
    fixtures = ['newsletters/fixtures/newsletters.json', ]

    def setUp(self):
        setup_test_environment()
        self.client = Client()
        self.recipient_email = 'pmorris96@gmail.com'
        self.location_id = 23

    def test_default_format(self):
        loc = SubscriberLocation.objects.get(pk=self.location_id)
        sub = Subscriber.objects.create(email_address=self.recipient_email, location=loc)
        sub.save()

        response = self.client.get('/newsletters/email/{}/'.format(sub.token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['content_type'], 'text/html')

    def test_html_format(self):
        loc = SubscriberLocation.objects.get(pk=self.location_id)
        sub = Subscriber.objects.create(email_address=self.recipient_email, location=loc)
        sub.save()

        response = self.client.get('/newsletters/email/{}/format/html/'.format(sub.token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['content_type'], 'text/html')

    def test_invalid_format(self):
        response = self.client.get('/newsletters/email/{}/format/XXXX'.format('abcd'))
        self.assertEqual(response.status_code, 404)


class WeatherTest(TestCase):

    def test_san_francisco_ca(self):
        w = Weather()
        city_weather = w.get_for_city('San Francisco', 'CA')

        # test keys: disposition, current_temp, current_sky, subject
        self.assertIn(city_weather['disposition'], Weather.subject.keys())
        self.assertIsInstance(city_weather['current_temp'], (int, float))
        self.assertRegex(city_weather['current_sky'], r'^[\w]+$')
        self.assertTrue(city_weather['current_sky_url'] > '')

    def test_disposition(self):
        # static attributes
        self.assertIn('disposition_good', Weather.__dict__.keys())
        self.assertIn('disposition_average', Weather.__dict__.keys())
        self.assertIn('disposition_bad', Weather.__dict__.keys())

        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))

        for disposition_name in ('disposition_good', 'disposition_bad', 'disposition_average'):
            # test static attribute is definitions
            self.assertIn(disposition_name, Weather.__dict__.keys())
            self.assertIsInstance(Weather.__dict__[disposition_name], str)

            # test in disposition
            disposition = Weather.__dict__[disposition_name]
            self.assertIn(disposition, Weather.subject)
            self.assertIsInstance(Weather.subject[disposition], str)
            self.assertGreater(Weather.subject[disposition], '')

        self.assertIsInstance(Weather.precipitating_icons, tuple)

    def test_dispose(self):

        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))
        variance = Weather.disposition_temp_variance_f

    def test_dispose_default(self):
        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))
        variance = Weather.disposition_temp_variance_f

        # average - no parameter sent
        self.assertEqual(Weather.dispose(), Weather.disposition_average)

    def test_dispose_good_warmer(self):
        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))
        variance = Weather.disposition_temp_variance_f

        # good - warmer
        avg_temp = 50
        self.assertEqual(
            Weather.disposition_good,
            Weather.dispose(
                avg_temp=avg_temp,
                current_temp=avg_temp + variance + 1
            )
        )

        # good warmer (exact/GTE)
        self.assertEqual(
            Weather.disposition_good,
            Weather.dispose(
                avg_temp=avg_temp,
                current_temp=avg_temp + variance
            )
        )

    def test_dispose_sunny(self):
        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))

        # good - warmer
        self.assertEqual(
            Weather.disposition_good,
            Weather.dispose(
                icon='sunny'
            )
        )

    def test_dispose_average_temp(self):
        variance = Weather.disposition_temp_variance_f

        # bad - colder
        avg_temp = 50
        self.assertEqual(
            Weather.disposition_average,
            Weather.dispose(
                avg_temp=avg_temp,
                current_temp=avg_temp
            )
        )


    def test_dispose_colder(self):
        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))
        variance = Weather.disposition_temp_variance_f

        # bad - colder
        avg_temp = 50
        self.assertEqual(
            Weather.disposition_bad,
            Weather.dispose(
                avg_temp=avg_temp,
                current_temp=avg_temp - variance - 1
            )
        )

        # bad - colder (exact/LTE)
        avg_temp = 50
        self.assertEqual(
            Weather.disposition_bad,
            Weather.dispose(
                avg_temp=avg_temp,
                current_temp=avg_temp - variance
            )
        )

    def test_dispose_precipitating(self):
        self.assertIn('disposition_temp_variance_f', Weather.__dict__.keys())
        self.assertIsInstance(Weather.disposition_temp_variance_f, (int, float))

        # bad - precipitating
        self.assertEqual(
            Weather.disposition_bad,
            Weather.dispose(
                icon='sleet'
            )
        )
