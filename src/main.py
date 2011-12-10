import webapp2

import htmlui
import restapi

# basic route for bringing up the app
lroutes = [ ('/', htmlui.ToDoHandler) ]

# add api routes, see restapi/__init__.py
lroutes.extend(restapi.restRoutes)

# create the application with these routes
app = webapp2.WSGIApplication(lroutes, debug=True)
