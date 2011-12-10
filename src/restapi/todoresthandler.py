#import os
from google.appengine.ext import webapp
from sleepy import Sleepy
from datamodel import ToDo

class ToDoRestHandler(webapp.RequestHandler):
    def get(self, aResource, aResourceArg, *args, **kwargs):
        Sleepy.gethandler(self, aResource, aResourceArg)

    def GetModelClass(self):
        return ToDo
    
    