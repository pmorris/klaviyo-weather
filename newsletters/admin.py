from django.contrib import admin

from .models import Subscriber, SubscriberLocation

admin.site.register(Subscriber)
admin.site.register(SubscriberLocation)