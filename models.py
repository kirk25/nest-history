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

from google.appengine.ext import ndb


class NestApiAuth(ndb.Model):
    """Models core auth parameters for accessing the Nest API."""
    auth_url = ndb.StringProperty()
    product_id = ndb.StringProperty()
    product_secret = ndb.StringProperty()


class Users(ndb.Model):
    """Models a user of this service."""
    access_token = ndb.StringProperty()
    email = ndb.StringProperty()
    nest_api_pin = ndb.StringProperty()
    token_valid_until = ndb.DateProperty()


class DataPoint(ndb.Model):
    """Models a single data point polled from a thermostat."""
    # TODO: consider a unique kind for each user/structure/where combo, so that
    #       that information doesn't have to be stored in every data point
    user = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    structure_id = ndb.StringProperty()
    where_id = ndb.StringProperty()
    ambient_temperature_f = ndb.IntegerProperty()
    target_temperature_f = ndb.IntegerProperty()
    humidity = ndb.IntegerProperty()
    hvac_state = ndb.StringProperty()
    fan_timer_active = ndb.BooleanProperty()
