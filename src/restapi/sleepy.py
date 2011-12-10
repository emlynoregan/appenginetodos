import datetime
from google.appengine.ext import db
import json
import logging

class Sleepy:
    @classmethod
    def FixRoutes(cls, aRoutes, aRouteBase = None):
        """ 
        Modifies routes to allow specification of id
        
        aRoutes should be pairs of resourcename, resource handler.
        
        This is modified to become pairs of route source, resource handler.
        
        aRouteBase is anything you want to prepend all route sources with. 
        
        eg: if you want all your route sources to begin with /api, use aRouteBase="/api" 
        
        Don't include a trailing slash in aRouteBase.
        """ 
        retval = []
        for lroute in aRoutes:
            lfixedRouteSource = '/(%s)(?:/(.*))?' % lroute[0]
            if aRouteBase:
                lfixedRouteSource = aRouteBase + lfixedRouteSource
            
            lfixedRoute = (lfixedRouteSource, lroute[1])
            retval.append(lfixedRoute)
        return retval

    @classmethod
    def ConstructDefaultTemplate(cls, aModelClass, aMaxDepth = 5):
        ltemplate = None

        if aMaxDepth > 0:
            ltemplate = {}
            
            lmodel = aModelClass()
                    
            for lkey, lprop in lmodel.properties().iteritems():
                if lkey[:1] is "_":
                    continue # ignore private props
                
                # Whatever it is. include it in the template.
                # this will cause issues with complex types (lists, reference), so
                # don't use it on them yet.
                ltemplate[lkey] = None
                
        return ltemplate

    SUPPORTEDDBTYPES = [
            db.IntegerProperty, 
            db.FloatProperty, 
            db.BooleanProperty,
            db.StringProperty
    ]

    @classmethod
    def ModelToJsonable(cls, aModel, aTemplate = None):
        """ 
        Use aTemplate to create json representation of aModel.
        If no aTemplate is given, a default template will be created.
        If no aModel is given, result will be None.
        """
        ljsonable = None

        if aModel:
            ljsonable = {}
            ljsonable['id'] = aModel.key().id() # We're going to work with numeric ids as resource identifiers

            ltemplate = aTemplate
            if not ltemplate:
                ltemplate = cls.ConstructDefaultTemplate(aModel.__class__)
                
            # here we have a template
            
            for lkey in ltemplate:
                if hasattr(aModel, lkey):
                    lvalue = getattr(aModel, lkey)
                    if lkey in aModel.properties():
                        # it's a datastore property
                        lprop = aModel.properties()[lkey]
                        if not type(lprop) in cls.SUPPORTEDDBTYPES:
                            raise TypeError("%s not supported" % type(lprop).__name__)
                        else:
                            ljsonable[lkey] = lvalue
                    else:
                        # it's some other kind of property.
                        # just guess that it's ok for now
                        ljsonable[lkey] = lvalue
        
        return ljsonable

    @classmethod
    def CheckMethodExists(cls, aObject, aMethodName, aMessage):
        if not hasattr(aObject, aMethodName):
            raise KeyError(aMessage)

    @classmethod
    def MethodExists(cls, aObject, aMethodName):
        return hasattr(aObject, aMethodName)

    @classmethod
    def gethandler(cls, aRestHandler, aResource, aResourceArg, *args, ** kwargs):
        try:
            cls.CheckMethodExists(aRestHandler, "GetModelClass", "Rest Handler must include a method GetModelClass()")                

            ltemplate = None
            if cls.MethodExists(aRestHandler, "GetTemplate"):
                ltemplate = aRestHandler.GetTemplate()

            if aResourceArg:
                lId = None
                try:
                    lId = int(aResourceArg)
                except:
                    raise ValueError("id must be an integer")

                lmodelClass = aRestHandler.GetModelClass()
                
                if not lmodelClass:
                    raise ValueError("GetModelClass() must not return None")
                
                cls.CheckMethodExists(lmodelClass, "get_by_id", "Class returned by GetModelClass() must support get_by_id")
                
                lmodel = lmodelClass.get_by_id(lId)

                if lmodel and cls.MethodExists(aRestHandler, "IsAuthorized"): 
                    if not aRestHandler.IsAuthorized(lmodel, *args, **kwargs):
                        lmodel = None

                if lmodel:
                    # here we have a model to return to the caller
                    lresultJsonable = cls.ModelToJsonable(lmodel, ltemplate)

                    if lresultJsonable:
                        cls.ReturnJsonable(aRestHandler, lresultJsonable)
                    else:
                        cls.ReturnNotFound(aRestHandler)
                else:
                    cls.ReturnNotFound(aRestHandler)
            else:
                lqry = aRestHandler.GetModelClass().all()

                if lqry and cls.MethodExists(aRestHandler, "ModifyQuery"):
                    lqry = aRestHandler.ModifyQuery(lqry, *args, **kwargs)
                
                lisAuthorizedMethod = None
                if cls.MethodExists(aRestHandler, "IsAuthorized"):
                    lisAuthorizedMethod = cls.IsAuthorized
                    
                lresultsJsonable = []

                for lmodel in lqry:
                    if (lisAuthorizedMethod is None) or lisAuthorizedMethod(lmodel, *args, **kwargs):
                        lresultsJsonable.append(cls.ModelToJsonable(lmodel, ltemplate))
                        
                cls.ReturnJsonable(aRestHandler, lresultsJsonable)
        except Exception, ex:
            logging.exception(ex)
            cls.ReturnException(aRestHandler, ex)
        
    @classmethod
    def ReturnException(cls, aRestHandler, aException):
        """ 
        http response with json representation of an exception
        """ 
        # should set status codes here
        aRestHandler.response.set_status(400)
        aRestHandler.response.body = repr(aException)
       
    @classmethod
    def ReturnJsonable(cls, aRestHandler, aJsonable):
        """ 
        http response with string representation of Json structure
        """ 
        loutput = json.dumps(aJsonable, sort_keys=True, indent=4)
        aRestHandler.response.out.write(loutput)

    @classmethod
    def ReturnNotFound(cls, aRestHandler):
        aRestHandler.response.set_status(404)
        aRestHandler.response.body = ""
    

