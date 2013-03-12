# -*- encoding: utf-8 -*-
from pyamf.remoting.amf0 import RequestProcessor, build_fault
import sys
from pyamf import remoting

django = __import__('django')
http = django.http
conf = django.conf
exceptions = django.core.exceptions
import_module = django.utils.importlib.import_module


class DjangoRequestProcessor(RequestProcessor):
    def __init__(self, gateway):
        super(DjangoRequestProcessor, self).__init__(gateway)
        self.loadMiddleware()

    def loadMiddleware(self):
        self._exception_middleware = []

        for middleware_path in conf.settings.GATEWAY_MIDDLEWARE:
            try:
                mw_module, mw_classname = middleware_path.rsplit('.', 1)
            except ValueError:
                raise exceptions.ImproperlyConfigured('%s isn\'t a middleware module' % middleware_path)
            try:
                mod = import_module(mw_module)
            except ImportError, e:
                raise exceptions.ImproperlyConfigured('Error importing middleware %s: "%s"' % (mw_module, e))
            try:
                mw_class = getattr(mod, mw_classname)
            except AttributeError:
                raise exceptions.ImproperlyConfigured('Middleware module "%s" does not define a "%s" class' % (mw_module, mw_classname))
            try:
                mw_instance = mw_class()
            except exceptions.MiddlewareNotUsed:
                continue

            if hasattr(mw_instance, 'process_exception'):
                self._exception_middleware.insert(0, mw_instance.process_exception)

    def buildErrorResponse(self, request, error=None):
        """
        Builds an error response.

        @param request: The AMF request
        @type request: L{Request<pyamf.remoting.Request>}
        @return: The AMF response
        @rtype: L{Response<pyamf.remoting.Response>}
        """
        if error is not None:
            cls, e, tb = error
        else:
            cls, e, tb = sys.exc_info()

        for middleware_method in self._exception_middleware:
            middleware_method(request, sys.exc_info())

        return remoting.Response(build_fault(cls, e, tb, self.gateway.debug),
                                 status=remoting.STATUS_ERROR)