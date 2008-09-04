from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import JSONResponder
from django_restapi.authentication import HttpBasicAuthentication
from django_restapi.receiver import JSONReceiver

from library.synapse.models import Document, Keyword, Source, Publisher, Publication, Employee, Department, EmployeeDepartment
from library.synapse.api.collections import PublicationCollection, PublicationEntry, KeywordCollection, KeywordEntry

json_source_resource = Collection(
    queryset = Source.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication()
    )
    
json_publisher_resource = Collection(
    queryset = Publisher.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication()
    )

json_document_resource = Collection(
    queryset = Document.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication()
    )

json_employee_resource = Collection(
    queryset = Employee.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication()
    )

json_department_resource = Collection(
    queryset = Department.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication()
    )

json_publication_resource = PublicationCollection(
    queryset = Publication.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication(),
    entry_class = PublicationEntry
    )

json_keyword_resource = KeywordCollection(
    queryset = Keyword.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = JSONResponder(paginate_by=200),
    receiver = JSONReceiver(),
    authentication = HttpBasicAuthentication(),
    entry_class = KeywordEntry
    )