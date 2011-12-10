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
        '''
        A Template is a dictionary, 
        which is a description of the properties which are published through the json interface.
        
        The set of keys in the dictionary are the properties to be included.
        Values are ignored.
        
        This method takes a model class, and returns the default template for that class, 
        ie: the one to use if none is provided.
        
        It includes all properties, minus any "private" ones (with a leading underscore)
        '''
        ltemplate = None

        if aMaxDepth > 0:
            ltemplate = {}
            
            lmodel = aModelClass()
                    
            for lkey in lmodel.properties(): 
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
            db.StringProperty,
            db.DateTimeProperty,
            db.DateProperty
    ]

    @classmethod
    def ParseDateTimeString(cls, string):
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ')

    @classmethod
    def ParseDateString(cls, string):
        return datetime.datetime.strptime(string, '%Y-%m-%dZ').date()

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
                        elif lvalue and type(lprop) == db.DateProperty or type(lprop) == db.DateTimeProperty:
                            ldateString = lvalue.isoformat()
                            # kludgy fix
                            if not hasattr(lvalue, "utcoffset") or not lvalue.utcoffset():
                                ldateString = ("%sZ" % ldateString)
                            ljsonable[lkey] = ldateString
                        else:
                            ljsonable[lkey] = lvalue
                    else:
                        # it's some other kind of property.
                        # just guess that it's ok for now
                        ljsonable[lkey] = lvalue
        
        return ljsonable

    @classmethod
    def JsonableToModel(cls, aJsonable, aModel, aTemplate = None):
        """
        Update a model instance from a Jsonable. 
        
        Can restrict allowed properties using optional Template.
        
        Returns a pair, comprising the Save list and the Delete list.
        
        The Save list is a list of models which require Putting to the datastore. Anything that's been touched.
        The first entry in the save list is guaranteed to be aModel.
        
        The Delete list is a list of any models which need to be deleted.
        """
        lsavemodels = []
        ldeletemodels = []
        lsaveanddeletearrays = (lsavemodels, ldeletemodels)
        
        if aModel:
            lsavemodels.append(aModel)
           
            if aJsonable:
                ltemplate = aTemplate
                if not ltemplate:
                    ltemplate = cls.ConstructDefaultTemplate(aModel.__class__)
                
                # here we have a template
                for lkey in ltemplate:
                    if lkey in aJsonable:
                        try:
                            # ok the key is in the template and the incoming jsonable, try setting the value
                            if hasattr(aModel, lkey):
                                lvalue = aJsonable[lkey]
                                
                                if lkey in aModel.properties():
                                    # it's a datastore property
                                    lprop = aModel.properties()[lkey]
                                    if not type(lprop) in cls.SUPPORTEDDBTYPES:
                                        raise TypeError("%s not supported" % type(lprop).__name__)
                                    elif type(lprop) is db.DateProperty:
                                        setattr(aModel, lkey, cls.ParseDateString(lvalue))
                                    elif type(lprop) is db.DateTimeProperty:
                                        setattr(aModel, lkey, cls.ParseDateTimeString(lvalue))
                                    else:
                                        setattr(aModel, lkey, lvalue)
                                else:
                                    # it's some other kind of property.
                                    # just guess that it's ok for now
                                    setattr(aModel, lkey, lvalue)
                        except Exception, ex:
                            raise ex.__class__("Error assigning '%s': %s" % (lkey, str(ex)))
                        
        return lsaveanddeletearrays

    @classmethod
    def ModelClassToMeta(cls, aModelClass, aTemplate = None):
        """
        This method takes a model Class, and an optional template (it'll call ConstructDefaultTemplate to make one if none is provide),
        and creates a Jsonable which contains a descriptions of the schema of the model Class.
        
        This is a dictionary, containing keys for every property in the Template, and values which are the type of the 
        property where that can be ascertained, or None where it can't.
        """
        lmeta = None
        
        ltemplate = aTemplate
        
        if aModelClass and not ltemplate:
            ltemplate =  cls.ConstructDefaultTemplate(aModelClass)

        if ltemplate:
            lmeta = {}
            
            lmodel = None
            if aModelClass:
                # it'll be convenient to have a blank model instance
                lmodel = aModelClass()
            
            # here we have a template
            for lkey in ltemplate:
                
                if lmodel and hasattr(lmodel, lkey):
                    lproperties = lmodel.properties()
                    if lkey in lproperties:
                        lprop = lmodel.properties()[lkey]
                        if "data_type" in type(lprop).__dict__:
                            lmeta[lkey] = type(lprop).__dict__["data_type"]. __name__.replace("basestring", "string")
                        else:
                            lmeta[lkey] = type(lprop).__name__
                    else:
                        lpropTypeMethodName = "proptype_%s" % lkey
                        if hasattr(lmodel, lpropTypeMethodName):
                            lpropTypeMethod = getattr(lmodel, lpropTypeMethodName)
                            lpropType = lpropTypeMethod()
                            lmeta[lkey] = lpropType.__name__.replace("str","string").replace("unicode","string")
                        else:
                            lmeta[lkey] = None # not a db field. Don't know anything about it.
                else:
                    raise ValueError("Incompatible template, field '%s' does not exist in model" % lkey)
            
        return lmeta

    @classmethod
    def CheckMethodExists(cls, aObject, aMethodName, aMessage):
        if not hasattr(aObject, aMethodName):
            raise KeyError(aMessage)

    @classmethod
    def MethodExists(cls, aObject, aMethodName):
        return hasattr(aObject, aMethodName)

    @classmethod
    def GetHandler(cls, aRestHandler, aResource, aResourceArg, *args, ** kwargs):
        try:
            cls.CheckMethodExists(aRestHandler, "GetModelClass", "Rest Handler must include a method GetModelClass()")                

            lmodelClass = aRestHandler.GetModelClass()
            
            if not lmodelClass:
                raise ValueError("GetModelClass() must not return None")

            ltemplate = None
            if cls.MethodExists(aRestHandler, "GetTemplate"):
                ltemplate = aRestHandler.GetTemplate()

            if aResourceArg and aResourceArg == "meta":
                ljsonable = cls.ModelClassToMeta(lmodelClass, ltemplate)
                cls.ReturnJsonable(aRestHandler, ljsonable)
            elif aResourceArg:
                lId = None
                try:
                    lId = int(aResourceArg)
                except:
                    raise ValueError("id must be an integer")
                
                cls.CheckMethodExists(lmodelClass, "get_by_id", "Class returned by GetModelClass() must support get_by_id")
                
                lmodel = lmodelClass.get_by_id(lId)

                if lmodel and cls.MethodExists(aRestHandler, "IsAuthorized"): 
                    if not aRestHandler.IsAuthorized(lmodel, *args, **kwargs):
                        lmodel = None

                if lmodel:
                    # here we have a model to return to the caller
                    lresultJsonable = cls.ModelToJsonable(lmodel, ltemplate)

                    cls.ReturnJsonable(aRestHandler, lresultJsonable)
                else:
                    cls.ReturnNotFound(aRestHandler)
            else:
                lqry = lmodelClass.all()

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
    def PutHandler(cls, aRestHandler, aResource, aResourceArg, *args, ** kwargs):
        try:
            cls.CheckMethodExists(aRestHandler, "GetModelClass", "Rest Handler must include a method GetModelClass()")                

            lmodelClass = aRestHandler.GetModelClass()
            
            if not lmodelClass:
                raise ValueError("GetModelClass() must not return None")

            ltemplate = None
            if cls.MethodExists(aRestHandler, "GetTemplate"):
                ltemplate = aRestHandler.GetTemplate()

            if aResourceArg:
                lId = None
                try:
                    lId = int(aResourceArg)
                except:
                    raise ValueError("id must be an integer")

                lincomingJsonable = cls.GetIncomingJsonable(aRestHandler)

                cls.CheckMethodExists(lmodelClass, "get_by_id", "Class returned by GetModelClass() must support get_by_id")
                
                lmodel = lmodelClass.get_by_id(lId)

                if lmodel and cls.MethodExists(aRestHandler, "IsAuthorized"): 
                    if not aRestHandler.IsAuthorized(lmodel, *args, **kwargs):
                        lmodel = None
                
                if lmodel:
                    lsaveanddeletearrays = cls.JsonableToModel(lincomingJsonable, lmodel, ltemplate)

                    lsavemodels = lsaveanddeletearrays[0]
                    ldeletemodels = lsaveanddeletearrays[1]

                    if cls.MethodExists(lmodel, "DecorateModel"):
                        lsavemodels = map(lmodel.DecorateModel, lsavemodels)
                    
                    db.put(lsavemodels)
                    db.delete(ldeletemodels)

                    lresultJsonable = cls.ModelToJsonable(lmodel, ltemplate)
                    
                    cls.ReturnJsonable(aRestHandler, lresultJsonable)
                else:
                    cls.ReturnNotFound(aRestHandler)
            else:
                raise KeyError("id is required")
        except Exception, ex:
            logging.exception(ex)
            cls.ReturnException(aRestHandler, ex)        

    @classmethod
    def PostHandler(cls, aRestHandler, aResource, aResourceArg, *args, ** kwargs):
        try:
            cls.CheckMethodExists(aRestHandler, "GetModelClass", "Rest Handler must include a method GetModelClass()")                

            lmodelClass = aRestHandler.GetModelClass()
            
            if not lmodelClass:
                raise ValueError("GetModelClass() must not return None")

            ltemplate = None
            if cls.MethodExists(aRestHandler, "GetTemplate"):
                ltemplate = aRestHandler.GetTemplate()

            if aResourceArg:
                raise KeyError("no arguments accepted for POST")
            else:
                lincomingJsonable = cls.GetIncomingJsonable(aRestHandler)

                lmodel = lmodelClass() # create a new model instance
                
                lsaveanddeletearrays = cls.JsonableToModel(lincomingJsonable, lmodel, ltemplate)

                lsavemodels = lsaveanddeletearrays[0]
                ldeletemodels = lsaveanddeletearrays[1]

                if cls.MethodExists(lmodel, "DecorateModel"):
                    lsavemodels = map(lmodel.DecorateModel, lsavemodels)
                
                db.put(lsavemodels)
                db.delete(ldeletemodels)

                lresultJsonable = cls.ModelToJsonable(lmodel, ltemplate)
                
                cls.ReturnJsonable(aRestHandler, lresultJsonable)
        except Exception, ex:
            logging.exception(ex)
            cls.ReturnException(aRestHandler, ex)        

    @classmethod
    def DeleteHandler(cls, aRestHandler, aResource, aResourceArg, *args, ** kwargs):
        try:
            cls.CheckMethodExists(aRestHandler, "GetModelClass", "Rest Handler must include a method GetModelClass()")                

            lmodelClass = aRestHandler.GetModelClass()
            
            if not lmodelClass:
                raise ValueError("GetModelClass() must not return None")

            if aResourceArg:
                lId = None
                try:
                    lId = int(aResourceArg)
                except:
                    raise ValueError("id must be an integer")

                cls.CheckMethodExists(lmodelClass, "get_by_id", "Class returned by GetModelClass() must support get_by_id")
                
                lmodel = lmodelClass.get_by_id(lId)

                if lmodel and cls.MethodExists(aRestHandler, "IsAuthorized"): 
                    if not aRestHandler.IsAuthorized(lmodel, *args, **kwargs):
                        lmodel = None
                    
                if lmodel:
                    # allow models to specify other models that need deleting
                    ldeleteList = [lmodel]
                    if cls.MethodExists(lmodel, "GetDeleteList"):
                        ldeleteList.append(lmodel.GetDeleteList())

                    db.delete(ldeleteList)

                    cls.ReturnNone(aRestHandler)
                else:
                    cls.ReturnNotFound(aRestHandler)
            else:
                raise KeyError("id is required")
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
        aRestHandler.response.body = "%s: %s" % (aException.__class__.__name__, str(aException))
       
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
    
    @classmethod
    def ReturnNone(cls, aRestHandler):
        aRestHandler.response.body = ""

    @classmethod        
    def GetIncomingJsonable(cls, aRestHandler):
        """
        Parse request body, return Json structure.
        """
        return json.loads(aRestHandler.request.body)

