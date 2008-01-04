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

import csv
import string

from django.http import HttpResponse
from django.template.loader import render_to_string

def CSV(results):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=synapse_results.csv'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Authors', 'Abstract', 'DOI', 'Source', 'Volume', 'Issue', 'Pages', 'Language', 'Year', 'Date', 'Document Type', 'ISNumber', 'ISType', 'DMT'])
    for doc in results:
        if hasattr(doc.dmt, 'name') and doc.dmt.name:
            dmt_name = doc.dmt.name
        else:
            dmt_name = ''
        if hasattr(doc, 'title') and doc.title:
            title = doc.title
        else:
            title = ''
        if hasattr(doc, 'author_names') and doc.author_names:
            author_names = doc.author_names
        else:
            author_names = ''
        if hasattr(doc, 'abstract') and doc.abstract:
            abstract = doc.abstract
        else:
            abstract = ''
        if hasattr(doc, 'doi') and doc.doi:
            doi = doc.doi
        else:
            doi = ''
        if hasattr(doc.source, 'name') and doc.source.name:
            source_name = doc.source.name
        else:
            source_name = ''
        if hasattr(doc, 'volume') and doc.volume:
            volume = doc.volume
        else:
            volume = ''
        if hasattr(doc, 'issue') and doc.issue:
            issue = doc.issue
        else:
            issue = ''
        if hasattr(doc, 'page_range') and doc.page_range:
            pages = doc.page_range
        else:
            pages = ''
        if hasattr(doc, 'language') and doc.language:
            language = doc.language
        else:
            language = ''
        if hasattr(doc, 'publish_year') and doc.publish_year:
            year = doc.publish_year
        else:
            year = ''
        if hasattr(doc, 'publish_date') and doc.publish_date:
            date = doc.publish_date
        else:
            date = ''
        if hasattr(doc, 'document_type') and doc.document_type:
            doc_type = doc.document_type
        else:
            doc_type = ''
        if hasattr(doc.source, 'is_number') and doc.source.is_number:
            isnum = doc.source.is_number
        else:
            isnum = ''
        if hasattr(doc.source, 'is_type') and doc.source.is_type:
            is_type = doc.source.is_type
        else:
            is_type = ''
        
        writer.writerow([title, author_names, abstract, doi, source_name, volume, issue, pages, language, year, date, doc_type, isnum, is_type, dmt_name])

        
    return response
    
    
def atom(results):
#     return response
    pass
    
class RISRecord(object):
    def __init__(self, result):
        self.TY = _map_document_type_to_TY(result.document_type)
        self.id = result.id
        self.title = result.title
        self.authors = [] #must populate this list
        if ';' in result.author_names:
            self.authors.extend(result.author_names.split(';'))
        elif result.author_names.count(',') > 1:
            self.authors.extend(result.author_names.split(','))
        # for author in authors, map(str.strip(), author), if ', ' not in author and ' ' in author, replace ' ' with ', '
        self.authors = [author.strip() for author in self.authors]
        
        a = []
        for author in self.authors:
            if ', ' not in author and ' ' in author:
                author = author.replace(' ', ', ')
            a.append(author)
        if a:
            self.authors = a



#         print self.authors
        self.publish_year = _format_year(result.publish_year)
        self.abstract = result.abstract
        self.keywords = result.keyword_set.all()
        if result.source:
            self.source = result.source.name
            self.is_number = result.fixed_is_number
            try:
                self.publisher = result.source.publisher_set.all()[0].name
            except IndexError:
                self.publisher = ''
        else:
            self.source = ''
            self.is_number = ''
            self.publisher = ''
        self.volume = result.volume
        self.issue = result.issue
        self.start_page = result.spage
        try:
            self.end_page = result.page_range.split('-')[1]
        except IndexError:
            self.end_page = ''

def _map_document_type_to_TY(doc_type):
    doc_type_map = {
    u"Article": u"JOUR",
    u"Conference Paper": u"CONF",
    u"Review Article": u"JOUR",
    u"Short Survey": u"JOUR",
    u"Editorial": u"JOUR",
    u"Book Chapter": u"CHAP",
    u"Book": u"BOOK",
    u"Article in Press": u"INPR",
    }
    return doc_type_map.get(doc_type, u"GEN")
    
def _format_year(year):
    #need to write code to make sure year is 4 digits
    yr = ''
    if year:
        assert len(str(year)) == 4
        assert str(year).isdigit()
        yr = "".join((str(year), "///"))
    return yr
    
def _ris_format(results):
    ris_results = []
    for doc in results:
        ris_results.append(RISRecord(doc))
    return ris_results
        



def RIS(results):
    #generate proper RIS formatted results
    ris_results = _ris_format(results)
    ris = render_to_string('synapse/ris_export.txt', {'results': ris_results})
    
    response = HttpResponse(mimetype='application/x-Research-Info-Systems')
    response['Content-Disposition'] = 'attachment; filename=synapse_results.ris'
    response.write(ris)
    return response
