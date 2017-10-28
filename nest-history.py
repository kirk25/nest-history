#!/usr/bin/env python

# MIT License

# Copyright (c) 2017 kirk25

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Python imports
import datetime
import json
import time
import os
import urlparse

# App Engine imports
from google.appengine.ext import deferred
from google.appengine.ext import ndb
import gviz_api
import jinja2
import logging
import requests
import requests_toolbelt.adapters.appengine
import webapp2

# App imports
import models

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

NEST_URL = 'https://developer-api.nest.com/'


class Collect(webapp2.RequestHandler):

    def _get_user_data_points(self, user, access_token):
        """Fetch one set of data points for a user and store them in datastore.

        One data point will be obtained and stored for each thermostat that a
        user has configured.

        Args:
          user: email address for the current user
          access_token: string access token for the user.
        """
        headers = {
            'content-type': "application/json",
            'authorization': "Bearer %s" % access_token,
            'cache-control': "no-cache",
            }
        # TODO: limit the request to only return fields we care about
        response = requests.request("GET", NEST_URL, headers=headers, 
                                    allow_redirects = False)
        if response.status_code == 307:
            response = requests.get(response.headers['Location'], 
                         headers=headers, allow_redirects=False)
        response.raise_for_status()
        #logging.info(response.text)
        try:
            result = response.json()
        except:
            # TODO: handle errors properly
            pass
        # TODO: can a valid response have no devices?  if so handle that
        thermostats = result['devices'].get('thermostats', None)
        # TODO: we should use the last_connection timestamp, and consider only
        # writing a sample when that gets updated.  Probably need to use
        # memcache to track that.
        now = datetime.datetime.now()
        if thermostats:
            for (device_id, data) in thermostats.items():
                ambient_temp = int(data['ambient_temperature_f'])
                target_temp = int(data['target_temperature_f'])
                fan_active = bool(data['fan_timer_active'])
                where = data.get('where_id', '')
                device_id = data['device_id']
                # last_connection has the format 2017-10-09T05:55:01.184Z
                last_connection = datetime.datetime.strptime(
                    data['last_connection'], '%Y-%m-%dT%H:%M:%S.%fZ')
                entity = models.DataPoint(user=user,
                                          structure_id=data['structure_id'],
                                          device_id=device_id,
                                          where_id=where,
                                          ambient_temperature_f=ambient_temp,
                                          target_temperature_f=target_temp,
                                          humidity=data['humidity'],
                                          hvac_state=data['hvac_state'],
                                          fan_timer_active=fan_active,
                                          timestamp=now,
                                          last_connection=last_connection,
                                          minute_ordinal=last_connection.minute,
                                          hour_ordinal=last_connection.hour,
                                          day_ordinal=last_connection.day)
                entity.put()
            

    def get(self):
        # TODO: consider sharding collection jobs into separate tasks
        # TODO: figure out how to detect/handle situations where one collection
        #       task takes longer than a minute, meaning the next will overlap
        users = models.Users.query()
        for user in users:
            logging.info('About to get data for user %s', user.email)
            self._get_user_data_points(user.email, user.access_token)


class LoadData(webapp2.RequestHandler):

    def get(self):
        description = [
            ('timestamp', 'datetime'),
            ('temperature', 'number'),
            ('humidity', 'number'),
        ]
        data = []

        query = models.DataPoint.query().filter(models.DataPoint.timestamp >= datetime.datetime.now() - datetime.timedelta(0,21600), models.DataPoint.where_id == '').order(models.DataPoint.timestamp)
        for point in query:
            data.append([point.timestamp, point.ambient_temperature_f,
                         point.humidity])

        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        self.response.write(data_table.ToJSonResponse())


class BackfillDataPoints(webapp2.RequestHandler):
    # Temporary handler to backfill device ids in the database.
    # Also the minuite ordinal, since it's convenient to do now.
    def get(self):
        deferred.defer(update_schema)
        

def update_schema(cursor=None, num_updated=0, batch_size=100):
    # Get all of the entities for this Model.
    query = models.DataPoint.query()
    data, next_cursor, more = query.fetch_page(
        batch_size, start_cursor=cursor)
    
    to_put = []
    for point in data:
        if (not point.last_connection or 
            point.last_connection == datetime.datetime.min):
            point.last_connection = datetime.datetime.min
            point.hour_ordinal = point.timestamp.hour
            point.day_ordinal = point.timestamp.day
        else:
            point.minute_ordinal = point.last_connection.minute
            point.hour_ordinal = point.last_connection.hour
            point.day_ordinal = point.last_connection.day
        to_put.append(point)

    # Save the updated entities.
    if to_put:
        ndb.put_multi(to_put)
        num_updated += len(to_put)
        logging.info(
            'Put {} entities to Datastore for a total of {}'.format(
                len(to_put), num_updated))

    # If there are more entities, re-queue this task for the next page.
    if more:
        deferred.defer(
            update_schema, cursor=next_cursor, num_updated=num_updated)
    else:
        logging.debug(
            'update_schema complete with {0} updates!'.format(
                num_updated))


class MainPage(webapp2.RequestHandler):

    def get(self):
        template_values = {
            'time': str(time.strftime('%m/%d/%Y %H:%M:%S %Z')),
            'loadURL': urlparse.urljoin(self.request.url, '/loadData')
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tasks/collect', Collect),
    ('/loadData', LoadData),
    ('/backfillDataPoints', BackfillDataPoints),
], debug=True)
