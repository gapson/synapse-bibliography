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

# Attribution:  General approach taken from similar code in Pybliographer
# http://www.pybliographer.org/, augmented by inspiration from David Mertz'
# Text Processing in Python.



from library.synapse.models import Document, Source, Publisher, Keyword, Institution, NameOrder, DiseaseManagementTeam, Publication, Employee
from library.synapse.util import split_name
from library.synapse.parsers import loader

import datetime
import re
import string

begin_field = re.compile (r'^(\w\w)\s(.*?)\r?$')
continue_field = re.compile (r'^\s{3,3}(.*?)\r?$')

class Record(object):
    def __init__(self):
        self.publication_type = ''
        self.document_type = ''
        self.document_subtype = ''
        self.title = []  # clean up into one long string
        self.authors = [] # clean up into one long string
        self.book_authors = [] # clean up into one long string
        self.source = ''
        self.publish_year = ''
        self.publish_date = ''
        self.volume = ''
        self.issue = ''
        self.pages = ''
        self.begin_page = ''
        self.end_page = ''
        self.language = ''
        self.isnumber = ''
        self.istype = ''
        self.publisher = ''
        self.doi = ''
        self.dmt = ''
        self.correspondence_address = ''
        self.esnumber = ''
        self.affiliations = []  #TODO: figure out how to handle these
        self.abstract = []  # clean up into one long string
        self.keywords = []  # clean up by splitting on delimiters
        
        # the following are throw-aways that contribute to self.keywords
        self.MC = []
        self.CC = []
        self.TA = []
        self.MI = []
        self.CH = []
        self.SC = []
        self.ID = []
        self.DE = []
        
    def clean(self):
        self.title = ' '.join(self.title)
        self.abstract = ' '.join(self.abstract)
        self.authors = ';'.join(self.authors)
        self.book_authors = ';'.join(self.book_authors)
        if self.isnumber:
            self.isnumber = self.isnumber.split()[0]
            self.isnumber = self.isnumber.rstrip(';')
        
        # join the keywords chunks together, split into list of keywords by
        # field-specific separator
        for field in (self.MC, self.CC, self.TA, self.CH, self.SC, self.ID, self.DE):
            self.keywords += ' '.join(field).split(';')
        
        self.keywords += ' '.join(self.MI).split(',')
        
        # clean extra whitespace from keywords
        self.keywords = map(string.strip, self.keywords)
        
        # clean empty keywords
        self.keywords = [word for word in self.keywords if word]
        
        # clean affiliations
        self.affiliations = ' '.join(self.affiliations) #.split(';')
        self.affiliations = self.affiliations.strip()
        # calculate pages, if needed
        if not self.pages:
            if self.begin_page and self.end_page:
                if not self.begin_page == self.end_page:
                    self.pages = '%s-%s' % (self.begin_page, self.end_page)
                else:
                    self.pages = self.begin_page
            elif self.begin_page:
                self.pages = self.begin_page
            elif self.end_page:
                self.pages = self.end_page

class ISIHandler(object):
    def __init__(self, content):
        self.parser = ISIParser(content)

        
    def parse(self):
        begin_sources = Source.objects.count()
        begin_publishers = Publisher.objects.count()
        begin_documents = Document.objects.count()
        begin_publications = Publication.objects.count()
        begin_employees = Employee.objects.count()
        begin_keywords = Keyword.objects.count()
        


        for line in self.parser.content:
            self.parser.handle_line(line)
        
        for record in self.parser.records:
            if record.document_type == 'Article in Press':
                continue

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


class ISIParser(object):
    def __init__(self, content):
        self.content = content
        self._store_upload()
        self.records = []

    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/ISI_file_%s.txt" % datetime.datetime.isoformat(datetime.datetime.now())
        isi_file_out = open(self.out_name, "wb")
        try:
            isi_file_out.write(self.content)
        except TypeError:
            isi_file_out.writelines(self.content)
        isi_file_out.close()
        fin = open(self.out_name, 'rU')
        self.content = fin.readlines()
        return None
        
    def handle_line(self, line):
        if line.strip () == '':
            return None
            
        field = begin_field.match(line)
        if field:
            tag, data = field.groups((1, 2))
            
            if tag in ('FN', 'VR', 'EF'):
                return None
            
            if tag == 'PT':
                self.record = Record()
                
            if tag == 'ER':
                self.record.clean()
                self.records.append(self.record)
                
            self.field_start(tag)
            self.field_data(data)
            return None
            
        continued_line = continue_field.match(line)
        if continued_line:
            self.field_data(continued_line.group(1))
            return None

    def field_start(self, tag):
        self.tag = tag
        self.data = []
        
    def field_data(self, data):
        self.data.append(data.rstrip())
        try:
            dispatch = getattr(self, self.tag)
            dispatch()

        except AttributeError, e:
            pass
        
    def PT(self):
        self.record.publication_type = self.data[0]
        
    def DT(self):
        self.record.document_type = self.data[0]
        
    def LT(self):
        self.record.document_subtype = self.data[0]
        
    def TI(self):
        self.record.title = self.data
        
    def AU(self):
        self.record.authors = self.data
        
    def BA(self):
        self.record.book_authors = self.data
        
    def BE(self):
        if self.tag != 'BE':
            self.record.book_authors.extend(self.data)
        else:
            self.record.book_authors = self.data
        
    def SO(self):
        self.record.source = self.data[0]
        
    def PY(self):
        self.record.publish_year = int(self.data[0][:4])
        
    def PD(self):
        self.record.publish_date = self.data[0]
        
    def VL(self):
        self.record.volume = self.data[0]
        
    def IS(self):
        self.record.issue = self.data[0]
        
    def PS(self):
        self.record.pages = self.data[0]
        
    def BP(self):
        self.record.begin_page = self.data[0]
        
    def EP(self):
        self.record.end_page = self.data[0]
        
    def LA(self):
        self.record.language = self.data[0]
        
    def BN(self):
        self.record.isnumber = self.data[0]
        self.record.istype = 'ISBN'
        
    def SN(self):
        self.record.isnumber = self.data[0]
        self.record.istype = 'ISSN'
        
    def C1(self):
        self.record.affiliations = self.data

    def PU(self):
        self.record.publisher = self.data[0]
        
    def AB(self):
        self.record.abstract = self.data
        
    # various keywords fields
    def MC(self):
        self.record.MC = self.data
                    
    def CC(self):
        self.record.CC = self.data
            
    def TA(self):
        self.record.TA = self.data

    def MI(self):
        self.record.MI = self.data

    def CH(self):
        self.record.CH = self.data

    def SC(self):
        self.record.SC = self.data

    def ID(self):
        self.record.ID = self.data
    
    def DE(self):
        self.record.DE = self.data
     