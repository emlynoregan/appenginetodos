import os
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp

class ToDoHandler(webapp.RequestHandler):

    def get(self):
        template_values = {}
                
        path = os.path.join(os.path.dirname(__file__), "todos.html")
        self.response.out.write(template.render(path, template_values))
        