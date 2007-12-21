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


from library.synapse.models import Document, Keyword, Employee
import string
import datetime
from django.db.models import Q

    
def search_all(search_data):
    q = Q()
    key_documents = None
    results = None

    if search_data['author'] and not search_data['author'] == 'Last Name, First':
        # parse author names
        # ex: 'Norton, L' or 'Norton, L; Begg, C'
        authors = search_data['author'].rstrip()
        authors = authors.rstrip(';')
        authors = authors.split(';')
        # ex: ['Norton, L'] or ['Norton, L', ' Begg, C']
        authors = map(string.strip, authors)
        document_id_lists = []
        intersection_set = set()

        for author in authors:
            document_ids = []
            pubs = []
            name_parts = author.split(', ')
            if len(name_parts) == 2:
                lname, fname = name_parts
                employees = Employee.objects.filter(last_name__iexact=lname, first_name__iexact=fname)
            else:
                lname = name_parts[0]
                employees = Employee.objects.filter(last_name__iexact=lname)
            for employee in employees:
                if pubs:
                    pubs = pubs | employee.publication_set.all()
                else:
                    pubs = employee.publication_set.all()
                
            for pub in pubs:
                document_ids.append(pub.document.id)
            document_id_lists.append(document_ids)
            for document_id_list in document_id_lists:
                if document_id_list:
                    document_id_set = set(document_id_list)
                    if intersection_set:
                        intersection_set = intersection_set.intersection(document_id_set)
                    else:
                        intersection_set = document_id_set
        q = q & Q(id__in=intersection_set)
        
    if search_data['journal'] and not search_data['journal'] == 'Ex: Blood':
        journals = search_data['journal'].split(';')
        journals = map(string.strip, journals)
        print "journals:", journals
        for journal in journals:
            q = q & Q(source__name__iexact=journal)
            
    if search_data['dmt'] and not search_data['dmt'] == '0':
        q = q & Q(dmt__id__exact=search_data['dmt'])
        
    if (search_data['year_start'] and not search_data['year_start'] == 'BLANK') or (search_data['year_end'] and not search_data['year_end'] == 'BLANK'):
        start = search_data['year_start']
        end = search_data['year_end']
        if not start or start == 'BLANK':
            start = datetime.datetime.now().year
        if not end or end == 'BLANK':
            end = datetime.datetime.now().year
        q = q & Q(publish_year__range=(start, end))
        
    if search_data['doc_type']:
        if isinstance(search_data['doc_type'], list):
            q = q & Q(document_type__in=search_data['doc_type'])
        else:
            q = q & Q(document_type__istartswith=search_data['doc_type'])
        
    if search_data['keywords'] and not search_data['keywords'] == 'Ex: melanoma':
        keywords = search_data['keywords'].split()
        title_documents = None
        abstract_documents = None
        keyword_documents = None
        for word in keywords:
            title_docs = Document.objects.filter(title__icontains=word)
            abstract_docs = Document.objects.filter(abstract__icontains=word)
            kwords = Keyword.objects.filter(term__icontains=word)
            keyword_doc_ids = [kw.document.id for kw in kwords]
            keyword_docs = Document.objects.filter(id__in=keyword_doc_ids)
            if title_documents:
                title_documents = title_docs & title_documents
            else:
                title_documents = title_docs
            if abstract_documents:
                abstract_documents = abstract_docs & abstract_documents
            else:
                abstract_documents = abstract_docs
            if keyword_documents:
                keyword_documents = keyword_documents & keyword_docs
            else:
                keyword_documents = keyword_docs
        
        if title_documents:
            if key_documents:
                key_documents = key_documents | title_documents
            else:
                key_documents = title_documents
                
        if abstract_documents:
            if key_documents:
                key_documents = key_documents | abstract_documents
            else:
                key_documents = abstract_documents
        if keyword_documents:
            if key_documents:
                key_documents = key_documents | keyword_documents
            else:
                key_documents = keyword_documents
            

    if key_documents:
        results = Document.objects.filter(q).select_related().order_by('-publish_year') & key_documents
    elif (hasattr(q, 'kwargs') and q.kwargs) or (hasattr(q, 'args') and q.args):
        results = Document.objects.filter(q).select_related().order_by('-publish_year')
    else:
        results = []
    return results
    