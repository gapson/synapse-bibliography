from django_restapi.model_resource import Collection, Entry
from django_restapi.responder import XMLResponder
from django_restapi.authentication import HttpBasicAuthentication
from django_restapi.receiver import XMLReceiver

from library.synapse.models import Document, Keyword, Source, Publisher, Publication, Employee, Department, EmployeeDepartment
from library.synapse.api.collections import PublicationCollection, PublicationEntry, KeywordCollection, KeywordEntry

xml_source_resource = Collection(
    queryset = Source.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication()
    )
    
xml_publisher_resource = Collection(
    queryset = Publisher.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication()
    )

xml_document_resource = Collection(
    queryset = Document.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication()
    )

xml_employee_resource = Collection(
    queryset = Employee.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication()
    )

xml_department_resource = Collection(
    queryset = Department.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication()
    )

xml_publication_resource = PublicationCollection(
    queryset = Publication.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication(),
    entry_class = PublicationEntry
    )

xml_keyword_resource = KeywordCollection(
    queryset = Keyword.objects.all(),
    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE'),
    responder = XMLResponder(paginate_by=200),
    receiver = XMLReceiver(),
    authentication = HttpBasicAuthentication(),
    entry_class = KeywordEntry
    )