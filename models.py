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
    structure_id = ndb.StringProperty()
    where_id = ndb.StringProperty()
    ambient_temperature_f = ndb.IntegerProperty()
    target_temperature_f = ndb.IntegerProperty()
    humidity = ndb.IntegerProperty()
    hvac_state = ndb.StringProperty()
    fan_timer_active = ndb.BooleanProperty()
