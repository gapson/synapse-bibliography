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
from django import db

def search_author(q, target):
    # parse author names
    # ex: 'Norton, L' or 'Norton, L; Begg, C'
    authors = target.rstrip()
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
    return q
    
def search_journal(q, target):
    journals = target.split(';')
    journals = map(string.strip, journals)
    for journal in journals:
        q = q & Q(source__name__iexact=journal)
    return q
    
def search_dmt(q, target):
    q = q & Q(dmt__id__exact=target)
    return q
    
def search_year(q, start_target=None, end_target=None):
    if not start_target or start_target == 'BLANK':
        start_target = datetime.datetime.now().year
    if not end_target or end_target == 'BLANK':
        end_target = datetime.datetime.now().year
    q = q & Q(publish_year__range=(start_target, end_target))
    return q
    
def search_doctype(q, target):
    if isinstance(target, list):
        q = q & Q(document_type__in=target)
    else:
        q = q & Q(document_type__istartswith=target)
    return q

def search_keyword(target):
    key_documents = None
    keywords = target.split()
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
    return key_documents
    
def search_keyword_sql(target):
    keywords = target.split()
    conn = db.connection
    crsr = conn.cursor()
    hits = []
#     doc_sql = "select id from synapse_document where title like '%%s%' or abstract like '%%s%'"
#     kw_sql = "select document_id from synapse_keyword where term like '%%s%'"
#     # naive -- loop over it    ---- do the harder job of figuring out how to concatenate the OR clauses together later
#     for kw in keywords:
#         crsr.execute(doc_sql, [kw, kw])
#         hits.extend(crsr.fetchall())
#         crsr.execute(kw_sql, [kw, kw])
#         hits.extend(crsr.fetchall())
    # hits at this point should contain all the document IDs of the docs that have one or more of the included keywords
    # this isn't what we want, but it's a start
    
    # take 2
    doc_sql = "select distinct id from synapse_document where (title like %s or abstract like %s)"
    doc_where = "(title like %s or abstract like %s)"
    where_clause = ""
    
    for i in xrange(len(keywords) - 1):
        where_clause = ' and '.join([where_clause, doc_where])
        
    doc_sql = ''.join((doc_sql, where_clause))
    
    # build a kw list with percents
    kwords = []
    for kw in keywords:
        kw = '%' + kw + '%'
        kwords.append(kw)
    
    # now build a list where each keyword is doubled
    params = []
    for kw in kwords:
        params.extend([kw, kw])
    
    crsr.execute(doc_sql, params)
#     print crsr.fetchall()
    results = crsr.fetchall()
#     print results
    for doc_id in results:
#         print "id: ", doc_id[0]
        hits.append(doc_id[0])
        
#     print "Title/abstract hits: ", hits
    
    kw_sql = "select distinct document_id from synapse_keyword where (term like %s)"
    kw_where = "(term like %s)"
    where_clause = ""
    
    for i in xrange(len(keywords) -1):
        where_clause = ' and '.join([where_clause, kw_where])
        
    kw_sql = ''.join((kw_sql, where_clause))
    
    crsr.execute(kw_sql, kwords)
#     print crsr.fetchall()
    results = crsr.fetchall()
#     print results
    for doc_id in results:
#         print "doc_id: ", doc_id[0]
        hits.append(doc_id[0])
    
#     print "Keyword hits: ", hits
    
    key_documents = Document.objects.filter(id__in=hits)
#     print key_documents
    if key_documents:
        return key_documents
    else:
        return "No results"
    
def search_all(search_data):
    q = Q()
    key_documents = None
    results = None

    if search_data['author'] and not search_data['author'] == 'Last Name, First':
        q = search_author(q, search_data['author'])
    
        
    if search_data['journal']:
        q = search_journal(q, search_data['journal'])
            
    if search_data['dmt'] and not search_data['dmt'] == '0':
        q = search_dmt(q, search_data['dmt'])
        
    if (search_data['year_start'] and not search_data['year_start'] == 'BLANK') or (search_data['year_end'] and not search_data['year_end'] == 'BLANK'):
        q = search_year(q, search_data['year_start'], search_data['year_end'])
        
    if search_data['doc_type']:
        q = search_doctype(q, search_data['doc_type'])
        
    if search_data['keywords']:
        key_documents = search_keyword_sql(search_data['keywords'])

#     if key_documents and key_documents != 'No results':
#         results = Document.objects.filter(q).select_related().order_by('-publish_year') & key_documents
#     elif key_documents == 'No results':
#         results = []
#     elif len(q):
#         print q
#         results = Document.objects.filter(q).select_related().order_by('-publish_year')
#         print results
#     else:
#         results = []
    # 1.  author search
    # 2.  keyword search
    # 3.  date search
    # 4.  combo search, with keywords
    
    if not key_documents:
        if len(q):
            results = Document.objects.filter(q).select_related().order_by('-publish_year')
        else:
            results = []
    else:
        if key_documents != 'No results':
            results = Document.objects.filter(q).select_related().order_by('-publish_year') & key_documents
        else:
            results = []

    return results
    