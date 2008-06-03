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

begin_record = re.compile(r'^<(\d+)>\r?$')    
begin_field = re.compile (r'^(\w\w)\s\s-\s(.*?)\r?$')
continue_field = re.compile (r'^\s{6,6}(.*?)\r?$')

class Record(object):
    def __init__(self):
        self.publication_type = []
        self.document_type = ''
        self.document_subtype = ''
        self.title = []  # clean up into one long string
        self.authors = [] # clean up into one long string
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
        self.affiliations = []  
        self.abstract = []  # clean up into one long string
        self.keywords = []  # clean up by splitting on delimiters
        
        # the following are throw-aways that contribute to self.keywords
        self.MH = []
        self.ID = []
        self.IT = []
        
    def _clean_keywords(self):
        # join the keywords chunks together, split into list of keywords by
        # field-specific separator
        self.keywords.extend(self.MH)
        
        self.keywords.extend(' '.join(self.ID).split(','))
        self.keywords.extend(' '.join(self.IT).split('.'))
        
        # clean extra whitespace from keywords
        self.keywords = map(string.strip, self.keywords)
        
        # clean empty keywords
        self.keywords = [word for word in self.keywords if word]
        return None
        
    def _clean_source(self):
        # this is hideous, readers beware
        # parse out source field
        # example 3: "Lippincott-Raven Publishers. (Philadelphia, PA) **1998; 373 p." -- CINAHL book format
        # example 4: "A clinical guide to AIDS and HIV (Wormser GP). Lippincott-Raven Publishers. (Philadelphia, PA) **1996; 359-78. (15 bib)" -- CINAHL book format
        # example 5: "Kanz, Lothar (Ed);  Weisel, Katja C (Ed);  Orlic, Donald (Ed);  Fibbe, Willem E (Ed). (2005). Hematopoietic stem cells V.  (pp. 51-59). x, 246 pp. New York, NY, US: New York Academy of Sciences. " -- PSYCINFO book format
        # example 6: "Puchalski, Christina M (Ed). (2006). A time for listening and caring: Spirituality and the care of the chronically ill and dying.  (pp. 183-192). xxii, 458 pp. New York, NY, US: Oxford University Press." -- PSYCINFO book format
        # example 7: "Primary health care of children (Fox JA). Mosby-Year Book, Inc.. (St. Louis, MO) **1997; 797-825. (6 bib)" -- CINAHL format
        
        if 'ook' in self.publication_type or 'Doctoral Dissertation' in self.publication_type:
            source_parts = [item for item in self.source[0].split('.') if item]
            if source_parts[1].startswith(' ('):
                # whole book
                self.source = self.title
                self.book_authors = self.authors
                self.publisher = source_parts[0].strip()
                locyear, pages = source_parts[1].split('; ')
                drop, self.publish_year = locyear.split('**')
                self.pages = pages.split()[0]
            else:
                # book chapter
                self.source = source_parts[0]
                self.publisher = source_parts[1].strip()
                for part in source_parts:
                    if '**' in part:
                        locyear, pages = part.split('; ')
#                 locyear, pages = source_parts[2].split('; ')
                        drop, self.publish_year = locyear.split('**')
                        self.pages = pages.split()[0]
                
        
        elif 'ournal' in self.publication_type:
        # example: "Cancer Practice: A Multidisciplinary Journal of Cancer Care. 1996 Mar-Apr; 4(2): 88-95. (9 ref)" -- CINAHL journal format
        # example 7: "Archives of Internal Medicine. 1999 Jul 26; 159(14): 1592-8, 1630-1. (15 ref)" -- CINAHL journal format
            # example 8: 'Journal of Clinical Oncology. 1999 Nov; 17(11s): Suppl: 44-52. (62 ref)'
            if isinstance(self.source, list):
                # if the source is split over two lines, it comes in as a len(source) > 1 list, 
                # so join it together into a string and work on that instead
                self.source = ''.join(self.source)
            print self.source
            self.source, pub, refs = self.source.split('.')
            self.source = self.source.strip()
            # pub = " 1996 Mar-Apr; 4(2): 88-95"
            # or pub = " 1999 Jul 26; 159(14): 1592-8, 1630-1"
            # or pub = " 1999 Nov; 17(11s): Suppl: 44-52"
            pubpages = pub.split(':')
            # pubpages = [' 1999 Jul 26; 159:(14)', '1592-8, 1630-1'] or [' 1999 Nov; 17(11s)', 'Suppl', ' 44-52']
            self.pages = ' '.join(pubpages[1:]).strip()
            # pub = " 1996 Mar-Apr; 4(2)"
            dates, volissue = pubpages[0].split(';')
            # dates = " 1996 Mar-Apr" or " 1999 Jul 26"
            dates = dates.strip()
            datestuff = dates.split()
            self.publish_year = datestuff[0]
            self.publish_date = ' '.join(datestuff[1:])
            # volissue = " 4(2)"
            volissue = volissue.strip()
            volissue = volissue.split('(')
            if len(volissue) > 1:
                self.volume, self.issue = volissue
            else:
                self.pages = ' '.join((volissue[0], self.pages))
            self.issue = self.issue.strip(')')
            return None

    def clean(self):
        self.title = ' '.join(self.title)
        self.title = self.title.strip('.')
        self.abstract = ' '.join(self.abstract)
        self.authors = ';'.join(self.authors)
        self.publication_type = ';'.join(self.publication_type)
        if not self.document_type:
            if ';' in self.publication_type:
                self.document_type = self.publication_type.split(';')[0]
            elif ',' in self.publication_type:
                self.document_type = self.publication_type.split(',')[0]
            else:
                self.document_type = self.publication_type
        self.affiliations = ' '.join(self.affiliations)
        if ' ' in self.isnumber:
            self.isnumber = self.isnumber.split()[0]
        self._clean_keywords()
        self._clean_source()
        if self.publisher.startswith('http'):
            self.publisher = ''


class CINAHLParser(object):
    def __init__(self, content):
        self.content = content
        self._store_upload()
        self.records = []
        self.tag = None
        self.data = []

    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/CINAHL_file_%s.txt" % datetime.datetime.isoformat(datetime.datetime.now())
        file_out = open(self.out_name, "wb")
        try:
            file_out.write(self.content)
        except TypeError:
            file_out.writelines(self.content)
        file_out.close()
        fin = open(self.out_name, 'rU')
        self.content = fin.readlines()
        return None
        
    def handle_line(self, line):
        if line.strip() == '':
            return None
            
        record_begin = begin_record.match(line)
        if record_begin:
            try:
                self.record.clean()
                self.records.append(self.record)
            except AttributeError, e:
                pass
            self.record = Record()
            return None
            
        field = begin_field.match(line)
        if field:
            tag, data = field.groups((1, 2))
                
            self.field_start(tag)
            self.field_data(data)
            return None
            
        continued_line = continue_field.match(line)
        if continued_line:
            self.field_data(continued_line.group(1))
            return None

    def field_start(self, tag):
        if self.tag == tag:
            return None
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
        self.record.publication_type = self.data  # occurs multiple times in Ovid files
        
    def DT(self):
        self.record.document_type = self.data[0]
                
    def TI(self):
        self.record.title = self.data
        
    def AU(self):
        self.record.authors = self.data
                
    def SO(self):
        self.record.source = self.data  # combined field, needs parsing
        
    def YR(self):
        self.record.publish_year = int(self.data[0])  # maybe add in length checking
                
    def VO(self):
        self.record.volume = self.data[0]
        
    def IP(self):
        self.record.issue = self.data[0]
        
    def PG(self):
        self.record.pages = self.data[0]
        
    def LG(self):
        self.record.language = self.data[0]
        
    def IB(self):
        self.record.isnumber = self.data[0]
        self.record.istype = 'ISBN'
        
    def IS(self):
        self.record.isnumber = self.data[0]
        self.record.istype = 'ISSN'

    def IT(self):
        self.record.IT = self.data
        
    def IN(self):
        self.record.affiliations = self.data

    def PU(self):
        self.record.publisher = self.data[0]
        
    def AB(self):
        self.record.abstract = self.data
        
    def DO(self):
        self.record.doi = self.data[0]
        
    # various keywords fields
    def MH(self):
        self.record.MH = self.data
                    
    def ID(self):
        self.record.ID = self.data
    




class CINAHLHandler(object):
    def __init__(self, content):
        self.parser = CINAHLParser(content)
        
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
            publisher = loader.create_publisher(record)
            source = loader.create_source(record, publisher)
            loader.associate_publisher_and_source(publisher, source)
            document = loader.create_document(record, source)
            loader.create_keywords(record, document)
            publications = loader.create_publications(record, document, nameorder_significant=True)
        
        
                                                                                                                                
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
