from todoresthandler import *
from sleepy import *

restRoutes = [
  ('todos', ToDoRestHandler)
]

restRoutes = Sleepy.FixRoutes(restRoutes)