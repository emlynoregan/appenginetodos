import webapp2

from htmlui import ToDoHandler
 
app = webapp2.WSGIApplication([
                            ('/', ToDoHandler)
                            ],
                            debug=True)
