from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

import re

from .models import Subscriber, SubscriberLocation, Weather

def index(request, error_message=""):

    context = {
        'location_group': SubscriberLocation.get_locations_by_state(100),
        'error_message': request.GET.get('msg', ''),
        'email_address': request.GET.get('email', ''),
        'location_id': request.GET.get('loc', '')
    }
    return render(request, 'newsletters/index.html', context)

@require_http_methods(["POST"])
def subscribe(request):
    # get data
    email_address = request.POST['email']
    location_id = request.POST['location']
    error_message = None

    if email_address is "":
        error_message = _('Please enter an email address')
    elif Subscriber.is_valid_email_address(email_address) is False:
        error_message = _('Please enter a valid email address')
    elif re.match('^[0-9]+$', location_id) is None:
        error_message = _('Please select a location')

    if error_message:
        return _subscribe_error(request, error_message=error_message)

    # validate and instantiate the location object
    try:
        location = SubscriberLocation.objects.get(pk=location_id)
    except SubscriberLocation.DoesNotExist:
        return _subscribe_error(request, error_message=_('Please select a location'))
    except:
        return _subscribe_error(request, error_message=_('Unexpected Error. Please try again'))

    # verify the subscriber does not exist and instantiate
    try:
        sub = Subscriber.objects.get(email_address=email_address)
        if sub.is_subscribed:
            error_message = _('{} is already subscribed for {}'.format(sub.email_address, sub.location))
            return _subscribe_error(request, error_message=error_message)
    except Subscriber.DoesNotExist:
        sub = Subscriber(email_address=email_address, is_subscribed=True, location=location)
        sub.save()
    return redirect(reverse('newsletters:subscriber', kwargs={'token': sub.token}))


def _subscribe_error(request, error_message, email_address="", location=""):
    qs = '?msg={}&email={}&loc={}'.format(error_message, request.POST['email'], request.POST['location'])
    return redirect(reverse('newsletters:index') + qs, permanent=False)

def subscriber(request, token):
    sub = get_object_or_404(Subscriber, token=token)
    context = {
        'subscriber': sub,
        'opt_in_uri': reverse('newsletters:index') + '?email={}&loc={}'.format(sub.email_address, sub.location_id),
        'opt_out_uri': reverse('newsletters:optout', kwargs={'token': sub.token}),
    }
    return render(request, 'newsletters/subscriber.html', context)

def optout(request, token):
    sub = get_object_or_404(Subscriber, token=token)
    sub.is_subscribed = False
    sub.save()
    context = {
        'subscriber': sub,
        'opt_in_uri': reverse('newsletters:index') + '?email={}&loc={}'.format(sub.email_address, sub.location_id),
    }
    return render(request, 'newsletters/optout.html', context)

def email(request, token, format='html'):

    if format in ('html', None):
        content_type = 'text/html'
        template_ext = 'html'
    elif format in ('text', 'txt'):
        content_type = 'text/plain'
        template_ext = 'txt'
    else:
        return HttpResponse('404 Not Found', status=404)

    sub = get_object_or_404(Subscriber, token=token)

    my_weather = Weather()
    city_weather = my_weather.get_for_city(city=sub.location.city, state=sub.location.state_abv)

    context = {
        'subscriber': sub,
        'subject': city_weather['subject'],
        'weather': city_weather,
        'content_type': content_type,
        'opt_out_url': '{protocol}://{host}{uri}'.format(
            protocol='http',
            host=request.get_host(),
            uri=reverse('newsletters:optout', kwargs={'token': sub.token})
        ),
    }
    return render(request, 'newsletters/email.{}'.format(template_ext), context, content_type=content_type)