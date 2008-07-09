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

begin_record = re.compile(r'^<(\d+)>\r?$')    #finish me -- done for the moment
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
        
    def _clean_keywords(self):
        # join the keywords chunks together, split into list of keywords by
        # field-specific separator
        self.keywords.extend(self.MH)
        
        self.keywords += ' '.join(self.ID).split(',')
        
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
        if 'ook' in self.publication_type:
            # it's a book
            source_parts = [item for item in self.source[0].split('.') if item]
            # PSYCINFO book format
            if source_parts[0].startswith('('):
                self.source = source_parts[1].strip()
            else:
                self.book_authors = source_parts[0].strip()
                self.source = source_parts[2].strip()
        
        elif 'ournal' in self.publication_type:
        # example: "Cancer Practice: A Multidisciplinary Journal of Cancer Care. 1996 Mar-Apr; 4(2): 88-95. (9 ref)" -- CINAHL journal format
        # example 2: "Preventive Medicine: An International Journal Devoted to Practice and Theory. Vol 36(1) Jan 2003, 71-84. " -- PSYCINFO journal format
        # example 7: "Archives of Internal Medicine. 1999 Jul 26; 159(14): 1592-8, 1630-1. (15 ref)" -- CINAHL journal format

            # handle as per PSYCINFO journal
            
            # self.source: ['Journal of Pain and Symptom Management. Vol 14(3, Suppl) Sep 1997, S27-S35.']
            self.source, pub, refs = self.source[0].split('.')
            # ['Journal of Pain and Symptom Management', ' Vol 14(3, Suppl) Sep 1997, S27-S35', '']
            self.source = self.source.strip()
            # pub = ' Vol 36(1) Jan 2003, 71-84'
            # or pub = ' Vol 27(2,Suppl) Aug 2004, 34-41'

            # self.source: ['Journal of Pain and Symptom Management. Vol 14(3, Suppl) Sep 1997, S27-S35.']
            # split(): ['Journal of Pain and Symptom Management', ' Vol 14(3, Suppl) Sep 1997, S27-S35', '']
            # self.source: Journal of Pain and Symptom Management
            # volissdate:  Vol 14(3, Suppl) Sep 199
            # too many volissdate bits: ['Vol', '14(3,', 'Suppl)', 'Sep', '199']
            # self.publish_year: 1997

            # pub = ' Vol 14(3, Suppl) Sep 1997, S27-S35'
            self.pages = pub[pub.rfind(',')+1:]
            self.pages = self.pages.strip()
            # self.pages = 'S27-S35'
            volissdate = pub[:pub.rfind(',')]
            volissdatebits = volissdate.split()
            if len(volissdatebits) == 4:
                toss, volissue, self.publish_date, self.publish_year = volissdatebits
            elif len(volissdatebits) == 3:
                toss, volissue, self.publish_year = volissdatebits
            elif len(volissdatebits) == 5:
                toss, volissue_a, volissue_b, self.publish_date, self.publish_year = volissdatebits
                volissue = ' '.join((volissue_a, volissue_b))
                # volissue = '14(3, Suppl)'
            else:
                print "too many volissdate bits:", volissdatebits
            print "self.publish_year:", self.publish_year
            # volissue = '36(1)'
            # or volissue = '(10(Suppl1)'
            volissue = ''
            if volissue:
                if volissue.startswith('('):
                    volissue = volissue.strip('(')
                self.volume, self.issue = volissue.split('(')
                self.issue = self.issue.strip(')')
        return None
                

    def clean(self):
        print "entering clean()"
        self.title = ' '.join(self.title)
        self.title = self.title.strip('.')
        self.abstract = ' '.join(self.abstract)
        self.authors = ';'.join(self.authors)
        self.publication_type = ';'.join(self.publication_type)
        self.affiliations = ';'.join(self.affiliations)
        if ' ' in self.isnumber:
            self.isnumber = self.isnumber.split()[0]
        self._clean_keywords()
        self._clean_source()
        if self.publisher.startswith('http'):
            self.publisher = ''


class PSYCINFOParser(object):
    def __init__(self, content):
        self.content = content
        self._store_upload()
        self.records = []
        self.tag = None
        self.data = []

    def _store_upload(self):
        # set the output file name to a standard name with a timestamp
        self.out_name = "/tmp/uploads/PSYCINFO_file_%s.txt" % datetime.datetime.isoformat(datetime.datetime.now())
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

    def AN(self):
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
        self.record.esnumber = self.data[0]
        
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
    




class PSYCINFOHandler(object):
    def __init__(self, content):
        self.parser = PSYCINFOParser(content)
        
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

