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
#     along with Synapse.  If not, see <http://www.gnu.org/licenses/>.

import string

from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned

from library.synapse.models import Publisher, Source, Document, Keyword, Publication
from library.synapse.models import DiseaseManagementTeam, Institution, NameOrder, Employee
from library.synapse.util import split_name, remove_punctuation, is_number_normalize

def create_publisher(record):
    publisher = None    
    if record.publisher:
        publisher, publisher_created = Publisher.objects.get_or_create(name=record.publisher)
    return publisher
    
def create_source(record, publisher):
    source = None
    source_created = False
    isnum = ''
    title = ''
    if record.isnumber:
        isnum = is_number_normalize(record.isnumber)
        
    if record.source:
        if record.source.isupper():
            title = record.source.title()
        else:
            title = record.source
        

    if record.istype:
        source, source_created = Source.objects.get_or_create(is_number=isnum,
                                                defaults={'name':title,
                                                          'publication_type':record.publication_type,
                                                          'is_type':record.istype})

    elif record.source:
        if record.isnumber:
            source, source_created = Source.objects.get_or_create(is_number=isnum,
                                                    defaults={'name':title,
                                                              'publication_type':record.publication_type})
        else:
            try:
                source, source_created = Source.objects.get_or_create(name=title,
                                                                      defaults={'publication_type':record.publication_type})
            except MultipleObjectsReturned:
                source = Source.objects.filter(name=title)[0]
            

    if source:
        modified = False
        if record.source and not source.name:
            source.name = title
            modified = True
        if record.publication_type and not source.publication_type:
            source.publication_type = record.publication_type
            modified = True
        if record.istype and not source.is_type:
            source.is_type = record.istype
            modified = True
        if record.esnumber and not source.es_number:
            source.es_number = is_number_normalize(record.esnumber)
            modified = True
        if modified:
            source.save()
    return source

def associate_publisher_and_source(publisher, source):
    if publisher:
        if source not in publisher.sources.all():
            publisher.sources.add(source)
            publisher.save()
    return None
    
def get_first_author(record):
    first_author = None
    if record.authors:
        first_author, drop, remainder = record.authors.partition(' ')
        first_author = first_author.rstrip().rstrip(',')
        first_author = remove_punctuation(first_author)
    return first_author
    
def map_document_type(document_type):
    doc_types = {'Review':'Review Article',
                 'Journal Article':'Article',
                 'Chapter':'Book Chapter',
                 'Book; Book Chapter':'Book Chapter',
                 'Meeting':'Conference Paper',
                 'Meeting Abstract':'Conference Paper',
                 'Conference Proceedings':'Conference Paper',
                 'Book; Meeting; Book Chapter':'Conference Paper',
                 'Erratum':'Other',
                 'Correction, Addition':'Other',
                 'Correction':'Other',
                 'Note':'Other',
                 'Letter':'Other',
                 'Editorial Material':'Editorial',
                 'Item About an Individual':'Other',
                 'Book Review':'Other',
                 'Reprint':'Other',
                 'Biographical-Item':'Other',
                 'News Item':'Other',
                 'Bibliography':'Other',
                 'Review-Book':'Other',
                 'Book Chapter; Meeting Paper':'Conference Paper',
                 'Article; Meeting':'Conference Paper',
                 'Section':'Other',
                 '':'Unspecified',
                 ' ':'Unspecified',
                 'Doctoral Dissertation':'Other',
                 None:'Unspecified'}
                 
    if document_type in doc_types:
        document_type = doc_types[document_type]
    return document_type
    
def create_document(record, source):
    document = None
    q = Q()
    if record.doi:
        documents = Document.objects.filter(doi__exact=record.doi)
        if len(documents) == 1:
            document = documents[0]
    if record.authors and record.pages and not document:
        # here's the first de-punctuated comparison point
        first_author = get_first_author(record)  # includes de-punctuation
        first_page = record.pages.split('-')[0].strip()
        if first_page and not first_page.isspace():
            documents = Document.objects.filter(page_range__isnull=False).filter(stripped_author_names__istartswith=first_author,
                  page_range__istartswith=first_page)
            if len(documents) == 1:
                document = documents[0]
    if record.authors and record.title and not document:
        # here's the second de-punctuated comparison point
        first_author = get_first_author(record) # includes de-punctuation
        stripped_title = remove_punctuation(record.title)
        documents = Document.objects.filter(stripped_author_names__istartswith=first_author,
              stripped_title__iexact=stripped_title)
        if len(documents) == 1:
            document = documents[0]


    if not document:
        document = Document.objects.create(title=record.title,
                                           author_names=record.authors,
                                           doi=record.doi)
                                                                
    modified = False
    if record.doi and not document.doi:
        document.doi = record.doi
        modified = True
    if record.title and not document.title:
        document.title = record.title
        modified = True
    if document.title and not document.stripped_title:
        document.stripped_title = remove_punctuation(document.title)
        modified = True
    if record.authors and not document.author_names:
        document.author_names = record.authors
        modified = True
    if record.authors and not document.stripped_author_names:
        # here's where we set the de-punctuated author
        document.stripped_author_names = remove_punctuation(record.authors)
        modified = True
    if record.source and not document.source:
        document.source = source
        modified = True
    if record.abstract and not document.abstract:
        document.abstract = record.abstract
        modified = True
    if record.volume and not document.volume:
        document.volume = record.volume
        modified = True
    if record.issue and not document.issue:
        document.issue = record.issue
        modified = True
    if record.pages and not document.page_range:
        document.page_range = record.pages
        modified = True
    if record.language and not document.language:
        document.language = record.language
        modified = True
    if record.publish_year and not document.publish_year:
        document.publish_year = record.publish_year
        modified = True
    if record.publish_date and not document.publish_date:
        document.publish_date = record.publish_date
        modified = True
    if record.document_type and not document.document_type:
        document.document_type = map_document_type(record.document_type)
        modified = True
    if record.document_subtype and not document.document_subtype:
        document.document_subtype = record.document_subtype
        modified = True
    if record.dmt and not document.dmt:
        document.dmt = DiseaseManagementTeam.objects.get(id=record.dmt)
        modified = True
    if record.affiliations and not document.affiliations:
        document.affiliations = record.affiliations
        modified = True
    if modified:
        document.save()
    return document

def create_keywords(record, document):
    for word in record.keywords:
        keyword, keyword_created = Keyword.objects.get_or_create(term=word, document=document)
    return None

def create_publications(record, document, nameorder_significant=False):
    # goal:  create a publication record for each author, populate record with appropriate
    # institution, affiliation, name order, and employee reference when and as possible
    
    # step 1:  create a publication record for each author
    publications = []
    authors = []
    if record.authors and ';' in record.authors:
        authors = record.authors.split(';')
    elif record.authors and ',' in record.authors and not ';' in record.authors:
        authors = record.authors.split(',')
        if len(authors) == 2 and len(authors[1]) == 1:
            authors = [record.authors]
    elif record.book_authors and ';' in record.book_authors:
        authors = record.book_authors.split(';')
    elif record.book_authors and ',' in record.book_authors and not ';' in record.authors:
        authors = record.book_authors.split(',')
    else:
        authors.append(record.authors)
    authors = map(string.strip, authors)
    for name in authors:
        nameorder = None
        if len(authors) == 1:
            nameorder, no_created = NameOrder.objects.get_or_create(order='Sole')
        elif name == authors[0] and not name == authors[-1]:
            nameorder, no_created = NameOrder.objects.get_or_create(order='First')
        elif name == authors[-1] and not name == authors[0]:
            nameorder, no_created = NameOrder.objects.get_or_create(order='Last')
        else:
            nameorder, no_created = NameOrder.objects.get_or_create(order='Contributor')
            
        publication, pub_created = Publication.objects.get_or_create(author_name=name.strip(),
                                                                     name_order=nameorder,
                                                                     document=document)
        publications.append(publication)

        # step 2: handle significant nameorder for CINAHL records
        if nameorder_significant and nameorder and nameorder.order in ('Sole', 'First'):
            publication.affiliation = record.affiliations
            address = record.affiliations
            if 'MSKCC' in address or 'Sloan-Kettering' in address or '1275 York' in address or 'Sloan Kettering' in address:
                publication.institution = Institution.objects.get(name='Memorial Sloan-Kettering Cancer Center')
            publication.save()


    # step 3: handle Correspondence Address, to catch anything missed earlier
    if record.correspondence_address:
        for pub in publications:
            if pub.author_name in record.correspondence_address:
                modified = False
                if not pub.affiliation:
                    pub.affiliation = record.correspondence_address
                    modified = True
                if not pub.institution:
                    address = record.correspondence_address
                    if 'MSKCC' in address or 'Sloan-Kettering' in address or '1275 York' in address or 'Sloan Kettering' in address:
                        pub.institution = Institution.objects.get(name='Memorial Sloan-Kettering Cancer Center')
                        modified = True
                if modified:
                    pub.save()
        


                                
    # step 4: populate each publication with appropriate employee, as possible
    for pub in publications:
        # handle PSYCINFO affiliations
        if record.affiliations:
            for affiliation in record.affiliations.split(';'):
                if pub.author_name in affiliation:
                    pub.affiliation = affiliation
                    if 'MSKCC' in affiliation or 'Sloan-Kettering' in affiliation or '1275 York' in affiliation or 'Sloan Kettering' in affiliation:
                        pub.institution = Institution.objects.get(name='Memorial Sloan-Kettering Cancer Center')
                    pub.save()
            # handle SCOPUS affiliations
            if len(record.affiliations.split(';')) == len(authors):
                name_index = None
                try:
                    name_index = authors.index(pub.author_name)
                except ValueError:  #names don't match
                    stripped_authors = map(remove_punctuation, authors)
                    name_index = stripped_authors.index(remove_punctuation(pub.author_name))
                if name_index:
                    pub.affiliation = record.affiliations.split(';')[name_index]
                    if 'MSKCC' in pub.affiliation or 'Sloan-Kettering' in pub.affiliation or '1275 York' in pub.affiliation or 'Sloan Kettering' in pub.affiliation:
                        pub.institution = Institution.objects.get(name='Memorial Sloan-Kettering Cancer Center')
                    pub.save()
        create_author(pub, pub.author_name)

                        

def create_author(publication, name):
    if not publication.author:
        fname, mname, lname = split_name(name)
        hits = 0
        emp = None
        institute = Institution.objects.get(name='Memorial Sloan-Kettering Cancer Center')

        hits = Employee.objects.filter(last_name__iexact=lname,
                                           first_name__istartswith=fname[:1]).count()
        if hits == 0:
            # No employee record found
            if publication.institution:
                emp = Employee.objects.create(first_name=fname, middle_name=mname, last_name=lname, currently_employed=False)
        elif hits == 1:
            # Suitable employee
            emp = Employee.objects.get(last_name__iexact=lname,
                                               first_name__istartswith=fname[:1])
        elif hits > 1:
            # Too many hits -- punt to human, don't guess
            return None
        
        if emp:
            publication.author = emp
            if not publication.institution:
                publication.institution = institute
            publication.save()
