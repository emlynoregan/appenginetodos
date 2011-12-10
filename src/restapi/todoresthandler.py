#import os
from google.appengine.ext import webapp
from sleepy import Sleepy
from datamodel import ToDo

class ToDoRestHandler(webapp.RequestHandler):
    def get(self, aResource, aResourceArg, *args, **kwargs):
        Sleepy.GetHandler(self, aResource, aResourceArg, *args, **kwargs)

    def put(self, aResource, aResourceArg, *args, **kwargs):
        Sleepy.PutHandler(self, aResource, aResourceArg, *args, **kwargs)

    def post(self, aResource, aResourceArg, *args, **kwargs):
        Sleepy.PostHandler(self, aResource, aResourceArg, *args, **kwargs)
    
    def delete(self, aResource, aResourceArg, *args, **kwargs):
        Sleepy.DeleteHandler(self, aResource, aResourceArg, *args, **kwargs)
    
    def GetModelClass(self):
        return ToDo
    
#    def GetTemplate(self):
#        return {
#            "text": None,
#            "order": None,
#            "done": None,
#            "modified": None
#        }
