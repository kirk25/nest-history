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

# App Engine imports
from google.appengine.ext import deferred
from google.appengine.ext import ndb
import logging

# App imports
import models


def update_schema(cursor=None, num_updated=0, batch_size=100):
    """Routine to update the schema for a model in datastore.

    This will generally be one-off code, and will be modified for each new
    schema update.

    Args:
      cursor: the Datastore query cursor, or None
      num_updated: the number of entities updated so far
      batch_size: the number of entities to update
    """
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
