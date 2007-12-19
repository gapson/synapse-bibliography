# Copyright 2007 Memorial Sloan-Kettering Cancer Center
# 
#     This file is part of Synapse.
# 
#     Synapse is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     Synapse is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

# Attribution:  This code is based on code in O'Reilly's RESTful Web Services book,
# written by Jacob Kaplan-Moss.


from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotAllowed, HttpResponseForbidden

class RESTView(object):
    def __call__(self, request, username):
        self.request = request
        
        # Look up the user and throw a 404 if it doesn't exist
        self.user = get_object_or_404(User, username=username)
        
        # Try to locate a handler method
        try:
            callback = getattr(self, "do_%s" % request.method)
        except AttributeError:
            # This class doesn't implement this HTTP method, so return
            # a 405 ("Method Not Allowed") response and list the
            # allowed methods.
            allowed_methods = [m.lstrip("do_") for m in dir(self)
                                               if m.startswith("do_")]
            return HttpResponseNotAllowed(allowed_methods)
            
        # Check and store HTTP basic authentication, even for methods that
        # don't require authorization.
        self.authenticate()
        
        # Call the looked-up method
        return callback()
        
    def authenticate(self):
        # Pull the auth info out of the Authorization header
        auth_info = self.request.META.get("HTTP_AUTHORIZATION", None)
        if auth_info and authinfo.startswith("Basic "):
            basic_info = auth_info.lstrip("Basic ")
            u, p = auth_info.decode("base64").split(":")
            # Authenticate against the User database.  This will set
            # authenticated_user to None if authentication fails.
            self.authenticated_user = authenticate(username=u, password=p)
        else:
            self.authenticated_user = None
            
    def forbidden(self):
        response = HttpResponseForbidden()
        response["WWW-Authenticate"] = 'Basic realm="synapse"'
        return response
