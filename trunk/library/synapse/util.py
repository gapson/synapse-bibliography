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
import csv, codecs, cStringIO
import re
from gremlins import *


class BulkParserDispatcher(object):
    def __init__(self, file_type, content, year, dmt):
        dispatch = getattr(self, file_type)
        self.parser = dispatch(content, year, dmt)
        
    def BIOSIS(self, content, year, dmt):
        from parsers.isi import ISIHandler
        return ISIHandler(content)
        
    def WOS(self, content, year, dmt):
        from parsers.isi import ISIHandler
        return ISIHandler(content)
        
    def PSYCINFO(self, content, year, dmt):
        from parsers.psycinfo import PSYCINFOHandler
        return PSYCINFOHandler(content)
        
    def CINAHL(self, content, year, dmt):
        from parsers.cinahl import CINAHLHandler
        return CINAHLHandler(content)
        
    def ENDNOTE(self, content, year, dmt):
        from parsers.endnote import EndNoteParser
        return EndNoteParser(content, dmt)
        
    def SCOPUS(self, content, year, dmt):
        from parsers.scopus import ScopusParser
        return ScopusParser(content)
        
    def EMPLOYEE(self, content, year, dmt):
        from parsers.employee import EmployeeParser
        return EmployeeParser(content, year)
    
    
def split_name(name):    
    """split the full name field into the various name parts"""
    lname = mname = fname = aname = ''
    # Separate the last name from the rest of the name on the comma
    # 'Duck', 'Daffy' = 'Duck,Daffy'.split(',')
    # Scopus example: 'Meropol N.J., Pazdur R., Vincent M., Willson J.K.V., Kelsen D.P., Douglass Jr. H.O., Erdi Yusuf E., Imbriaco Massimo'
    # EndNote examples: 'Renshaw, A. A.' or 'Rosai, J.'
    if ',' in name:
        name_parts = name.split(',')
    else:
        name_parts = name.split()
    name_parts = map(string.strip, name_parts)
    if len(name_parts) > 2:
        period_location = name_parts[1].find('.')
        if period_location > 1:  # if "Jr."
            lname = ' '.join((name_parts[0], name_parts[1]))
            aname = ''.join(name_parts[2:])
        else:
            lname = name_parts[0]
            aname = ' '.join(name_parts[1:])
            
    elif len(name_parts) == 2:
        lname, aname = name_parts
    else: # wacky one-word name without commas
        lname = name_parts[0]
    # If there are no spaces in the name
    # if 'Daffy'.find(' ') == -1:
    if aname and aname.find(' ') == -1:
        # special case for ISI initial concatenations (e.g. 'Smith, PM')
        if aname.isupper() and len(aname) > 1:
            fname = aname[:1]
            mname = aname[1:]
            if mname == '.':
                mname = ''
        else:
        # then the first name is the rest of the name and middle is blank
        # fname = 'Daffy'
            fname = aname
            mname = ''
    elif not aname:
        pass
    else:
        # else split the name on the first space, give the first chunk to first name
        # and assign the rest to the middle name, while dropping the space separator
        # aname = "John Quincy Wilbur"
        # "John", " ", "Quincy Wilbur"
        fname, drop, mname = aname.partition(' ')
    return (fname, mname, lname)


def remove_punctuation(phrase):
    allowed = string.ascii_letters + string.digits + string.whitespace
    stripped_phrase = [character for character in phrase if character in allowed]
    stripped_phrase = ''.join(stripped_phrase)
    stripped_phrase = stripped_phrase.lower()
    return stripped_phrase

def is_number_normalize(is_number):
    isnum = is_number
    isnum = isnum.rjust(8, '0')
    if len(isnum) == 8:
        isnum = '-'.join((isnum[:4], isnum[4:]))
    if len(isnum) > 17:
        isnum = isnum[:17]
    return isnum


