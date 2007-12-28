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
from django.http import HttpResponse

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
    response = HttpResponse(mimetype='application/xml+atomfeed')  #Read up on syndication framework, also read up on Atom format
    response['Content-Disposition'] = 'attachment; filename=synapse_results.csv'
