from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_init
from django.core.cache import cache
import re
import uuid
from wunderground.models import Almanac, Conditions, Forecast

class SubscriberLocation(models.Model):

    class Meta:
        db_table = 'newsletter_subscriber_locations'

    city = models.TextField(max_length=200)
    state_abv = models.TextField(max_length=15)
    country = models.TextField(max_length=2, default='US')
    population = models.PositiveIntegerField('Last Known Population', null=True)
    population_estimate = models.PositiveIntegerField('Estimated Population', null=True, db_index=True)
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    def __str__(self):
        return self.city_state()

    @staticmethod
    def get_locations_by_state(limit):
        locations = list(SubscriberLocation.objects.order_by('-population_estimate')[:100])
        # assert isinstance(locations.sort, object)
        locations.sort(key=lambda x: x.state_abv + x.city)

        nested_locations = {}
        for location in locations:
            if location.state() not in nested_locations:
                nested_locations[location.state()] = []

            nested_locations[location.state()].append(location)

        return nested_locations

    @staticmethod
    def state_name(state_abv):
        states = {
            'AK': 'Alaska',
            'AL': 'Alabama',
            'AR': 'Arkansas',
            'AS': 'American Samoa',
            'AZ': 'Arizona',
            'CA': 'California',
            'CO': 'Colorado',
            'CT': 'Connecticut',
            'DC': 'District of Columbia',
            'DE': 'Delaware',
            'FL': 'Florida',
            'GA': 'Georgia',
            'GU': 'Guam',
            'HI': 'Hawaii',
            'IA': 'Iowa',
            'ID': 'Idaho',
            'IL': 'Illinois',
            'IN': 'Indiana',
            'KS': 'Kansas',
            'KY': 'Kentucky',
            'LA': 'Louisiana',
            'MA': 'Massachusetts',
            'MD': 'Maryland',
            'ME': 'Maine',
            'MI': 'Michigan',
            'MN': 'Minnesota',
            'MO': 'Missouri',
            'MP': 'Northern Mariana Islands',
            'MS': 'Mississippi',
            'MT': 'Montana',
            'NA': 'National',
            'NC': 'North Carolina',
            'ND': 'North Dakota',
            'NE': 'Nebraska',
            'NH': 'New Hampshire',
            'NJ': 'New Jersey',
            'NM': 'New Mexico',
            'NV': 'Nevada',
            'NY': 'New York',
            'OH': 'Ohio',
            'OK': 'Oklahoma',
            'OR': 'Oregon',
            'PA': 'Pennsylvania',
            'PR': 'Puerto Rico',
            'RI': 'Rhode Island',
            'SC': 'South Carolina',
            'SD': 'South Dakota',
            'TN': 'Tennessee',
            'TX': 'Texas',
            'UT': 'Utah',
            'VA': 'Virginia',
            'VI': 'Virgin Islands',
            'VT': 'Vermont',
            'WA': 'Washington',
            'WI': 'Wisconsin',
            'WV': 'West Virginia',
            'WY': 'Wyoming'
        }

        if isinstance(state_abv, str) is False:
            return ''
        elif state_abv.upper() in states:
            return states[state_abv.upper()]
        else:
            return ''

    def state(self):
        return SubscriberLocation.state_name(self.state_abv)

    def city_state(self):
        return '{}, {}'.format(self.city, self.state_abv)



class Subscriber(models.Model):

    class Meta:
        db_table = 'newsletter_subscribers'

    email_address = models.CharField(max_length=200, unique=True)
    location = models.ForeignKey(SubscriberLocation, null=True)
    is_subscribed = models.BooleanField(default=True, db_index=True)
    token = models.CharField(max_length=40, unique=True)
    subscribed_at = models.DateTimeField('Subscribed At', auto_now_add=True)
    unsubscribed_at = models.DateTimeField('Unsubscribed At', null=True, blank=True)
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    def __str__(self):
        return '{email} -- {location}'.format(
            email=self.email_address,
            location=self.location,
        )

    def clean(self):
        # validate the format of the email address
        if self.is_valid_email_address(self.email_address) is False:
            raise ValidationError(_('Invalid Email Address'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super(self.__class__, self).save(*args, **kwargs)

    @staticmethod
    def is_valid_email_address(email_address):
        # validate email address (http://emailregex.com/)
        pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        return re.match(pattern, email_address) is not None

def subscriber_post_init(**kwargs):
    instance = kwargs.get('instance')
    if instance.token == '':
        instance.token = uuid.uuid4().hex

post_init.connect(subscriber_post_init, Subscriber)


class Weather:

    disposition_good = 'good'
    disposition_average = 'averge'
    disposition_bad = 'bad'

    precipitating_icons = ('sleet', 'rain', 'snow', 'tstorms')

    # the variation in degrees Farienheit allowed for swaying the disposition
    disposition_temp_variance_f = 5

    # TODO: move these values to a config file for easy manipulation
    subject = {
        disposition_good: "It's nice out! Enjoy a discount on us.",
        disposition_average: 'Enjoy a discount on us.',
        disposition_bad: "Not so nice out? That's okay, enjoy a discount on us."
    }

    def get_for_city(self, city, state):

        # for testing
        # return {'disposition': 'good',
        #                 'subject': "Not so nice out? That's okay, enjoy a discount on us.",
        #                 'current_temp': 53, 'current_sky': 'sunny',
        #                 'current_sky_url': 'https://icons.wxug.com/i/c/j/clear.gif'}
        # TODO: try to fetch from from cache/shelve first

        # get from Wunderground API
        a = Almanac()
        aa = a.get(city, state)

        c = Conditions()
        cc = c.get(city, state)

        f = Forecast()
        ff = f.get(city, state)

        disposition = __class__.dispose(
            sky=cc['weather'],
            icon=cc['icon'],
            current_temp=float(cc['temp_f']),
            avg_temp=float(aa['temp_high']['normal']['F'])
        )

        rval = {
            'disposition': disposition,
            'subject': __class__.subject[disposition],
            'current_temp': int(cc['temp_f']),
            'current_sky': cc['weather'].lower(),
            'current_sky_url': Conditions.get_icon_url(cc['icon'])
        }
        return rval

    @staticmethod
    def dispose(**kwargs):

        current_temp = kwargs.get('current_temp', None)
        average_temp = kwargs.get('avg_temp', None)
        icon = kwargs.get('icon', None)
        # sky is not used currently, replaced with icon (for now)
        sky = kwargs.get('sky', None)

        # good if sunny
        if icon == 'sunny':
            return __class__.disposition_good

        # good (or bad) if temp is 5 degrees above (or below) average
        if isinstance(current_temp, (int, float)) and isinstance(average_temp, (int, float)):
            temp_diff = current_temp - average_temp

            if temp_diff >= __class__.disposition_temp_variance_f:
                return __class__.disposition_good
            elif temp_diff <= (__class__.disposition_temp_variance_f * -1):
                return __class__.disposition_bad

        # bad if precipitating
        if icon is not None and icon in __class__.precipitating_icons:
            return __class__.disposition_bad

        return __class__.disposition_average





