'''
Created Dec 10, 2011

@author: emlyn o'regan
'''
from google.appengine.ext import db

class ToDo(db.Model):
    text = db.StringProperty()
    order = db.IntegerProperty()
    done = db.BooleanProperty()
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty(auto_now = True)
