from django.core.management.base import BaseCommand
from django.core import mail
from django.core.cache import cache
from django.template.loader import render_to_string

from newsletters.models import Subscriber, Weather

class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):

        # TODO: configure cache to use memcached
        # cache object expiration - 15 minutes
        cache_expiry = 60 * 15

        weather = Weather()

        emails_sent = 0
        locations_queried = 0

        # open a connection to the outgoing mail server
        with mail.get_connection() as connection:
            for sub in Subscriber.objects.filter(is_subscribed=True):
                print('subscriber: {} ({}, {})'.format(sub.email_address, sub.location.city, sub.location.state_abv))

                # get the weather info from cache if available, else from API
                city_weather = cache.get(sub.location_id)

                if city_weather is None:
                    # data is not cached, fetch it from the source
                    city_weather = weather.get_for_city(city=sub.location.city, state=sub.location.state_abv)
                    cache.set(sub.location_id, city_weather, cache_expiry)
                    locations_queried += 1

                # get html and plain text email bodies
                context = {
                    'subscriber': sub,
                    'subject': city_weather['subject'],
                    'weather': city_weather
                }
                msg_html = render_to_string('newsletters/email.html', context=context)
                msg_plain = render_to_string('newsletters/email.txt', context=context)

                # send the email
                msg = mail.EmailMultiAlternatives(
                    city_weather['subject'],
                    msg_plain,
                    'email@philmorris.net',
                    [sub.email_address],
                    ['pmorris@gmail.com', 'email@philmorris.net'],
                    cc=['pmorris96@gmail.com', 'email@philmorris.net'],
                    connection=connection
                )
                msg.attach_alternative(msg_html, "text/html")
                msg.send()
                emails_sent += 1

        self.stdout.write('Successfully sent {} emails for {} locations'.format(emails_sent, locations_queried))