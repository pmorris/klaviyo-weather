# Weather App

My first Django site, built on a SQLite database for portability. I'd recommend moving another datastore for production use.. The site contains 2 modules which were written from scratch. I realize there are several existing newsletter modules which could have been dropped in, but I chose to write these to gain a deeper understanding of Python and Django, and to demonstrate coding design principles and strategies. Here's an overview of the 2 modules. The will be explained in more detail below:
1. Newsletters - Allows the users to opt in and out of newsletters. Also sends newsletter to those subscribed
2. Wunderground - A python client for the Weather Undgerground API

## Configuration
The only configuration necessary is to configure the outgoing SMTP server settings in `./codechallenge/settings.py`.

## Newsletter Module
This module as web interfaces which allow users to subscribe and unsubscribe from receiving the newsletter. Only one subscription is allowed per email address and each can only be associated with a single location. The 100 most populous US cities are available for selection. An additional 204 cities are available in the database which can be made visible with a slight modification within the code. The hidden cities can be manually linked to any subscriber's account through the admin interface.

I have also provided a management command (`sendnewsletter`) which will send newsletters to all active subscribers, individually. To run this process efficiently, the pertinent weather information is being stored to a local cache in memory. With more time, and with sufficient need, I'd prefer to store these data in Memcache with a 15 minute expiration. The other performance consideration is the method in which the emails are sent. There seem to be several ways to send emails in Python, I felt it was important to send all of the email to a single connection, per each run. I also chose to construct each recipient's email individually for simplicity, and to allow more personal content to be delivered within each email. There's likely some caching which could be implemented here to prevent from reading the templates from disk with each email.

## Wunderground Module
This module serves as a client to the Weather Underground API. It currenly only supports endpoints for Almanac, Conditions and Forecast as those were all that were needed for this project. If this were to be distributed or to be used more heavily, all other API methods, and corresponding tests would need to be added.

## Final thoughts
1. both modules have a few hard-coded values (e.g. the number of cities displayed, the Wunderground API key, the cache timeout). With more time I would move all of these constants to configuration files within each respective module.
2. I did not build any tests, nor provide any test fixtures for the `sendnewsletter` management command due to time constraints. That's likely the top priority before considering a production release. At this time that code is fairly simple (~60 lines) and most of the code within is covered under existing unit tests.
3. With the current implementation the Weather.get_for_city method in Newsletters could have been a static method, however the original thought was to build the caching mechanism into the Weather class. I later abandoned that approach for increased flexibility for future developers.
4. While writing the credits section below, I've realized that I failed to include the proper credit within the newsletter emails, per the [Terms of Service](https://www.wunderground.com/weather/api/d/terms.html) outlined by Weather Underground. This would have to be addressed before a production release.

## Credits
1. The [Weather Underground API](https://www.wunderground.com/weather/api)
2. The city population data is from the US Census, via [Wikipedia](https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population)
3. The styling of the newsletter web templates was based the CSS in the signup page by [WayoshiM](https://github.com/WayoshiM/klaviyo).