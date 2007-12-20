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




from xml.etree import cElementTree as e
import datetime
import string
import codecs

from library.synapse.models import Document, Source, Publisher, Keyword, Institution, NameOrder, DiseaseManagementTeam, Publication, Employee
from library.synapse.util import split_name, kill_gremlins
from library.synapse.parsers import loader

class Record(object):
    def __init__(self, rec):
        self.publication_type = ''
        self.document_type = ''
        self.document_subtype = ''
        self.title = ''
        self.authors = [] 
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
        self.affiliations = ''
        self.doi = ''
        self.abstract = ''  # clean up into one long string
        self.keywords = []  # clean up by splitting on delimiters
        self.CH = ''
        self.tradenames = ''
        self.manufacturers = ''
        self.correspondence_address = ''
        self.dmt = ''
        self._populate(rec)

    def _populate(self, rec):
        pub_type = rec.find('ref-type').get('name')
        pub_type = pub_type.split()
        if len(pub_type) == 1:
            self.document_type = pub_type[0]
        else:
            self.publication_type = pub_type[0]
            self.document_type = pub_type[1]
        
        self.title = rec.findtext('titles/title/style')
        
        author_elements = rec.findall('contributors/authors/author')
        self.authors = [author.findtext('style') for author in author_elements]
        self.authors = '; '.join(self.authors)
        
        self.source = rec.findtext('periodical/full-title/style')
        if not self.source:
            self.source = rec.findtext('titles/secondary-title/style')
        self.publish_year = rec.findtext('dates/year/style')
        self.volume = rec.findtext('volume/style')
        self.issue = rec.findtext('number/style')
        self.pages = rec.findtext('pages/style')
        notes = rec.findtext('notes/style')
        if notes:
            notes_parts = notes.split('\r')
            for item in notes_parts:
                if item.endswith('N)'):
                    self.isnumber = item.split()[0]
                    self.istype = item.split()[1].strip().strip('(').strip(')')
                if item.startswith('Language'):
                    self.language = item.split(':')[1].strip()
                if item.startswith('Chemicals'):
                    self.CH = item.split(':')[1].strip()
                if item.startswith('Tradenames'):
                    self.tradenames = item.split(':')[1].strip()
                if item.startswith('Manufacturers'):
                    self.manufacturers = item.split(':')[1].strip()
                if item.startswith('Correspondence'):
                    self.correspondence_address = item.split(':')[1].strip()
        kw = rec.findall('keywords/keyword')
        for k in kw:
            self.keywords.append(k.findtext('style'))
        if self.CH:
            self.keywords.extend(self.CH.split(';'))
        if self.tradenames:
            self.keywords.extend(self.tradenames.split(';'))
        if self.manufacturers:
            self.keywords.extend(self.manufacturers.split(';'))
        if self.keywords:
            self.keywords = map(string.strip, self.keywords)
        self.abstract = rec.findtext('abstract/style')
        self.publisher = rec.findtext('publisher/style')
        self.affiliations = rec.findtext('auth-address/style')
        lang = rec.findtext('language/style')
        if lang:
            self.language = lang
        doc_type = rec.findtext('work-type/style')
        if doc_type:
            self.document_type = doc_type
        self.esnumber = rec.findtext('electronic-resource-num/style')
        is_number = rec.findtext('isbn/style')
        if is_number:
            self.isnumber = is_number
        
        if self.issue is None:
            self.issue = ''
        if self.abstract is None:
            self.abstract = ''
        if self.pages is None:
            self.pages = ''
        if self.volume is None:
            self.volume = ''
        if self.affiliations is None:
            self.affiliations = ''
            


class EndNoteParser(object):
    def __init__(self, content, dmt):
        self.content = content
        self.dmt = dmt
        self._store_upload()
        self.records = []
        return None
        
        
    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/endnote_file_%s.xml" % datetime.datetime.isoformat(datetime.datetime.now())
        file_out = codecs.open(self.out_name, "wb", encoding='ascii', errors='replace')
        file_out.write(kill_gremlins(self.content))
        file_out.close()
        return None

    def get_tree(self):
        fin = open(self.out_name, 'rU')
        root = e.XML(fin.read())
        return root
        
    def create_records(self):
        root = self.get_tree()
        records = root.findall('records/record')
        for rec in records:
            record = Record(rec)
            if self.dmt and self.dmt != ' ' and self.dmt != 'BLANK' and self.dmt != '0':
                record.dmt = self.dmt
            self.records.append(record)


        
    def parse(self):
        begin_sources = Source.objects.count()
        begin_publishers = Publisher.objects.count()
        begin_documents = Document.objects.count()
        begin_publications = Publication.objects.count()
        begin_employees = Employee.objects.count()
        begin_keywords = Keyword.objects.count()
        
        # get the records in the file, parse the XML into a usable record, perform functions on the record
        self.create_records()
        
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
