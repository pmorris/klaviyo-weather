from django.conf.urls import url

from . import views

app_name = 'newsletters'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^subscribe$', views.subscribe, name='subscribe'),
    url(r'^subscriber/(?P<token>[A-z0-9\-]+)/$', views.subscriber, name="subscriber"),
    url(r'^optout/(?P<token>[A-z0-9\-]+)/$', views.optout, name="optout"),
    url(r'^email/(?P<token>[A-z0-9\-]+)/(format/(?P<format>[a-z]+)/)?$', views.email, name="newsletter"),
]