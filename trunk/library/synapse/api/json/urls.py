from django.conf.urls.defaults import *

from json import *



urlpatterns = patterns('',
    (r'^employees/(?P<employee_id>\d+)/publications/(?P<publication_id>\d+)/$', json_publication_resource, {'is_entry':True}),
    (r'^employees/(?P<employee_id>\d+)/publications/$', json_publication_resource, {'is_entry':False}),
    (r'^documents/(?P<document_id>\d+)/keywords/(?P<keyword_id>\d+)/$', json_keyword_resource, {'is_entry':True}),
    (r'^documents/(?P<document_id>\d+)/keywords/$', json_keyword_resource, {'is_entry':False}),
    (r'^sources/(.*)/?$', json_source_resource),
    (r'^publishers/(.*)/?$', json_publisher_resource),
    (r'^documents/(.*)/$', json_document_resource),
    (r'^documents/$', json_document_resource),
    (r'^employees/(.*)/$', json_employee_resource),
    (r'^employees/$', json_employee_resource),
    (r'^departments/(.*)/?$', json_department_resource),
)
