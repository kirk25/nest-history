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
import json
import time
import os

# App Engine imports
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

NEST_URL = "https://developer-api.nest.com/"


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
            'postman-token': "88859d7d-8bfb-f966-67cf-d4f89e9fc7a4"
            }
        response = requests.request("GET", NEST_URL, headers=headers, 
                                    allow_redirects = False)
        if response.status_code == 307:
            response = requests.get(response.headers['Location'], 
                         headers=headers, allow_redirects=False)
        response.raise_for_status()
        logging.info(response.text)
        try:
            result = response.json()
        except:
            # TODO: handle errors properly
            pass
        # TODO: can a valid response have no devices?  if so handle that
        thermostats = result['devices'].get('thermostats', None)
        if thermostats:
            for (device_id, data) in thermostats.items():
                ambient_temp = int(data['ambient_temperature_f'])
                target_temp = int(data['target_temperature_f'])
                fan_active = bool(data['fan_timer_active'])
                where = data.get('where_id', '')
                entity = models.DataPoint(user=user,
                                          structure_id=data['structure_id'],
                                          where_id=where,
                                          ambient_temperature_f=ambient_temp,
                                          target_temperature_f=target_temp,
                                          humidity=data['humidity'],
                                          hvac_state=data['hvac_state'],
                                          fan_timer_active=fan_active)
                entity.put()
            

    def get(self):
        # TODO: consider sharding collection jobs into separate tasks
        # TODO: figure out how to detect/handle situations where one collection
        #       task takes longer than a minute, meaning the next will overlap
        users = models.Users.query()
        for user in users:
            logging.info('About to get data for user %s, "%s"', 
                         user.email, user.access_token)
            self._get_user_data_points(user.email, user.access_token)


class MainPage(webapp2.RequestHandler):

    def get(self):
        template_values = {
            'time': str(time.strftime('%m/%d/%Y %H:%M:%S')),
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tasks/collect', Collect),
], debug=True)
