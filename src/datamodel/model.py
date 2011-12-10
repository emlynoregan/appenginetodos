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

    def __init__(self, *args, **kwargs):
        db.Model.__init__(self, *args, **kwargs)
        if self.done is None:
            self.done = False

#    @property
#    def calculated(self):
#        return "the value"
#    
#    def proptype_calculated(self):
#        return str