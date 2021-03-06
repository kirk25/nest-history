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
from google.appengine.api import memcache
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
import update_schema

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
                self.addDeviceIfNecessary(device_id, user)
                # last_connection has the format 2017-10-09T05:55:01.184Z
                last_connection = datetime.datetime.strptime(
                    data['last_connection'], '%Y-%m-%dT%H:%M:%S.%fZ')
                if self.shouldUpdate(device_id, last_connection):
                    ambient_temp = int(data['ambient_temperature_f'])
                    target_temp = int(data['target_temperature_f'])
                    fan_active = bool(data['fan_timer_active'])
                    where = data.get('where_id', '')
                    device_id = data['device_id']
                    entity = models.DataPoint(
                        user=user,
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
                    logging.info('Adding data point for device %s', device_id)
                else:
                    logging.info('Skipping duplicate data point for device %s',
                                 device_id)
            
    def addDeviceIfNecessary(self, device_id, user):
        # NDB's caching means this won't hit datastore very often.
        query = models.Device.query(models.Device.device_id == device_id)
        if not query.iter().has_next():
            models.Device(user=user, device_id=device_id).put()

    def shouldUpdate(self, device_id, timestamp):
        key = '%s:last_connection' % device_id
        prev = memcache.get(key)
        if not prev or prev != timestamp:
            ok = memcache.set(key, timestamp)
            return True
        else:
            return False

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
        device_id = self.request.GET.get('device')
        tqx = self.request.GET.get('tqx')
        if not device_id or not tqx:
            self.response.status = '404 Not Found'
            return

        tqx_dict = {}
        for pair in tqx.split(';'):
            key, val = pair.split(':')
            tqx_dict[key] = val

        query = models.DataPoint.query().filter(
            models.DataPoint.device_id == device_id,
            models.DataPoint.last_connection >= 
            datetime.datetime.now() - datetime.timedelta(0,21600)).order(
            models.DataPoint.last_connection)

        data = []
        for point in query:
            data.append([point.last_connection, point.ambient_temperature_f,
                         point.humidity])

        description = [
            ('timestamp', 'datetime'),
            ('temperature', 'number'),
            ('humidity', 'number'),
        ]
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        self.response.write(data_table.ToJSonResponse(req_id=tqx_dict['reqId']))


class BackfillDataPoints(webapp2.RequestHandler):
    # Temporary handler to backfill device ids in the database.
    # Also the minuite ordinal, since it's convenient to do now.
    def get(self):
        deferred.defer(update_schema.update_schema)
        

class MainPage(webapp2.RequestHandler):

    def get(self):
        # TODO: filter by the active user
        query = models.Device.query()
        device_list = [device.device_id for device in query]

        template_values = {
            'time': str(time.strftime('%m/%d/%Y %H:%M:%S %Z')),
            'loadURL': urlparse.urljoin(self.request.url, '/loadData'),
            'devices': device_list,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tasks/collect', Collect),
    ('/loadData', LoadData),
    ('/backfillDataPoints', BackfillDataPoints),
], debug=True)
