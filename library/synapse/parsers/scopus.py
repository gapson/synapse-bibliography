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
    
from library.synapse.models import Document, Source, Publisher, Keyword, Institution, NameOrder, DiseaseManagementTeam, Publication, Employee

import csv
import datetime
import string
import codecs

from library.synapse.util import kill_gremlins
from library.synapse.parsers import loader


def split_name(name):    
    """split the full name field into the various name parts"""
    lname = mname = fname = aname = ''
    # Separate the last name from the rest of the name on the comma
    # Scopus example: 'Meropol N.J., Pazdur R., Vincent M., Willson J.K.V., Kelsen D.P., Douglass Jr. H.O.'
    # Scopus Correspondence Address example: "Meropol, N.J."
    # stupid junk in Scopus' processing: " Scott McNutt N."
    # more irregularities:  "Erdi Yusuf E., Humm John L., Imbriaco Massimo, Yeung Henry, Larson Steven M."
    if ',' in name:
    	name_parts = name.split(',')
    else:
        name_parts = name.split()
        
    name_parts = map(string.strip, name_parts)
    
    # before we get to counting parts, we need to check for initials v. spelled-out names
    # nix that, count then check for initials
    if len(name_parts) > 2:
        period_location = name_parts[1].find('.')
        if period_location > 1:  # if 'Jr.' (or 'Dr.' or 'Mrs.' -- bug possibility)
            lname = ' '.join((name_parts[0], name_parts[1]))
            aname = ''.join(name_parts[2:])

        else:
            lname = name_parts[0]
            aname = ' '.join(name_parts[1:])
    
        
    elif len(name_parts) == 2:
        lname, aname = name_parts
        
    else: # wacky one-word name
        lname = name_parts[0]
        
    # lname = 'Meropol' or 'Douglass Jr.'
    # aname = 'N.J.' or 'R.' or 'J.K.V.' or 'Mcnutt N.' or 'Yusuf E.' or 'Henry'
    aname = aname.split()
    # aname = ['N.J.'] or ['R.'] or ['J.K.V.'] or ['McNutt', 'N.'] or ['Henry']
    aname_parts = []
    for part in aname:
        initials = part.split('.')
        for item in initials:
            if item:
                aname_parts.append(item)
    aname_parts = map(string.strip, aname_parts)
    fname = aname_parts[0]
    if len(aname_parts) > 1:
        mname = ' '.join(aname_parts[1:])

    return (fname, mname, lname)



class Record(object):
    def __init__(self):
        self.publication_type = ''
        self.document_type = ''
        self.document_subtype = ''
        self.title = ''
        self.authors = ''
        self.book_authors = ''
        self.source = ''
        self.publish_year = ''
        self.publish_date = ''
        self.volume = ''
        self.issue = ''
        self.pages = ''
        self.language = ''
        self.isnumber = ''
        self.esnumber = ''
        self.istype = ''
        self.publisher = ''
        self.doi = ''
        self.dmt = ''
        self.correspondence_address = ''
        self.affiliations = '' 
        self.abstract = ''
        self.keywords = []  # clean up by splitting on delimiters
        


class ScopusParser(object):
    def __init__(self, content):
        self.content = content
        self._store_upload()
        self.records = []
        return None
        
        
    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/scopus_file_%s.csv" % datetime.datetime.isoformat(datetime.datetime.now())
        file_out = codecs.open(self.out_name, "wb", encoding='ascii', errors='replace')
        file_out.write(kill_gremlins(self.content))
        file_out.close()
        return None

    def get_reader(self):
        # assume user has whacked off the first few lines (5 normally) 
        # turn it into a CSV instance
        reader = csv.DictReader(open(self.out_name, "Ur"))
#         reader = UnicodeDictReader(open(self.out_name, "Ur"))
        return reader

    def create_record(self, row):
        record = Record()
        record.publisher = row['Publisher']
        if row['ISSN']:
            record.isnumber = row['ISSN']
            record.istype = 'ISSN'
            record.publication_type = 'Journal'
        elif row['ISBN']:
            record.isnumber = row['ISBN'].split(';')[0]
            record.istype = 'ISBN'
            record.publication_type = 'Book'
        record.source = row['Source title']
        record.pages = '%s-%s' % (row['Page start'], row['Page end'])
        record.title = row['Title']
        record.doi = row['DOI']
        record.authors = row['Authors']
        record.abstract = row['Abstract']
        record.volume = row['Volume']
        record.issue = row['Issue']
        record.language = row['Language of Original Document']
        record.publish_year = row['Year']
        record.document_type = row['Document Type']
        record.affiliations = row['Affiliations']
        for word in row['Author Keywords'].split(';'):
            record.keywords.append(word.strip())
        for word in row['Index Keywords'].split(';'):
            record.keywords.append(word.strip())
        record.keywords.append(row['Molecular Sequence Numbers'].strip())
        for word in row['Chemicals/CAS'].split(';'):
            record.keywords.append(word.strip())
        for word in row['Tradenames'].split(';'):
            record.keywords.append(word.strip())
        for word in row['Manufacturers'].split(';'):
            record.keywords.append(word.strip())
        record.correspondence_address = row['Correspondence Address']
        
        return record
    
    def parse(self):
        
        begin_sources = Source.objects.count()
        begin_publishers = Publisher.objects.count()
        begin_documents = Document.objects.count()
        begin_publications = Publication.objects.count()
        begin_employees = Employee.objects.count()
        begin_keywords = Keyword.objects.count()
        
        for row in self.get_reader():
            self.records.append(self.create_record(row))
            
        for record in self.records:
            publisher = loader.create_publisher(record)
            source = loader.create_source(record, publisher)
            loader.associate_publisher_and_source(publisher, source)
            document = loader.create_document(record, source)
            loader.create_keywords(record, document)
            publications = loader.create_publications(record, document)
                                                                                                                                                 
        end_sources = Source.objects.count()
        end_publishers = Publisher.objects.count()
        end_documents = Document.objects.count()
        end_publications = Publication.objects.count()
        end_employees = Employee.objects.count()
        end_keywords = Keyword.objects.count()
        
        new_sources = end_sources - begin_sources
        new_publishers = end_publishers - begin_publishers
        new_documents = end_documents - begin_documents
        new_publications = end_publications - begin_publications
        new_employees = end_employees - begin_employees
        new_keywords = end_keywords - begin_keywords

        status = {'employees_created':new_employees, 'documents_created':new_documents, 'publishers_created':new_publishers,
        'sources_created':new_sources, 'publications_created':new_publications, 'keywords_created':new_keywords}
        return status

