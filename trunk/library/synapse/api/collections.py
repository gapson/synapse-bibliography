from django_restapi.model_resource import Collection, Entry

from library.synapse.models import Employee, Document

class PublicationCollection(Collection):
    def read(self, request):
#         print request
        employee_id = int(request.path.split("/")[5])
#         print employee_id
        filtered_set = self.queryset._clone()
        filtered_set = filtered_set.filter(author__id=employee_id)
        return self.responder.list(request, filtered_set)
    
    def get_entry(self, employee_id, publication_id):
        print employee_id
        employee = Employee.objects.get(id=int(employee_id))
        publication = employee.publication_set.get(pk=int(publication_id))
        return PublicationEntry(self, publication)

    def get_url(self):
        return reverse(self, (), {'employee_id':self.model.author.id})

class PublicationEntry(Entry):
    
    def get_url(self):
        publication_id = self.model.id
        return reverse(self.collection, (), {'employee_id':self.model.author.id, 'publication_id':publication_id})
        
class KeywordCollection(Collection):
    def read(self, request):
        doc_id = int(request.path.split("/")[5])
        filtered_set = self.queryset._clone()
        filtered_set = filtered_set.filter(document_id=doc_id)
        return self.responder.list(request, filtered_set)
        
    def get_entry(self, document_id, keyword_id):
        document = Document.objects.get(id=int(document_id))
        keyword = document.keyword_set.get(pk=int(keyword_id))
        return KeywordEntry(self, keyword)
        
    def get_url(self):
        return reverse(self, (), {'document_id':self.model.document.id})
        
class KeywordEntry(Entry):
    def get_url(self):
        keyword_id = self.model.id
        return reverse(elf.collection, (), {'document_id':self.model.document.id, 'keyword_id':keyword_id})
        
