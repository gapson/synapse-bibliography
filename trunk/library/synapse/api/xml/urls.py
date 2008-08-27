from django.conf.urls.defaults import *

from xml import *



urlpatterns = patterns('',
    (r'^employees/(?P<employee_id>\d+)/publications/(?P<publication_id>\d+)/$', xml_publication_resource, {'is_entry':True}),
    (r'^employees/(?P<employee_id>\d+)/publications/$', xml_publication_resource, {'is_entry':False}),
    (r'^documents/(?P<document_id>\d+)/keywords/(?P<keyword_id>\d+)/$', xml_keyword_resource, {'is_entry':True}),
    (r'^documents/(?P<document_id>\d+)/keywords/$', xml_keyword_resource, {'is_entry':False}),
    (r'^sources/(.*)/?$', xml_source_resource),
    (r'^publishers/(.*)/?$', xml_publisher_resource),
    (r'^documents/(.*)/$', xml_document_resource),
    (r'^documents/$', xml_document_resource),
    (r'^employees/(.*)/$', xml_employee_resource),
    (r'^employees/$', xml_employee_resource),
    (r'^departments/(.*)/?$', xml_department_resource),
)
