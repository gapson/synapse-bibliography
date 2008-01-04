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
from itertools import chain

from django import newforms as forms
from django.utils.encoding import force_unicode
from django.utils.html import escape

from library.synapse.models import DiseaseManagementTeam, Document

BULK_LOAD_TYPES = (
    ('BIOSIS', 'Biosis'),
    ('WOS', 'Web of Science'),
    ('PSYCINFO', 'PsycInfo'),
    ('CINAHL', 'CINAHL Nursing/Allied Health'),
    ('ENDNOTE', 'EndNote XML'),
    ('SCOPUS', 'Scopus CSV'),
    ('EMPLOYEE', 'Employee Listing CSV')
)

YEAR_START = [
    ('BLANK', 'All articles'),
    ]
    
YEAR_END = [
    ('BLANK', 'Present'),
    ]

YEAR = [
    ('BLANK', ''),
    ]
    
    
DMT = [('0', '')]
DMT.extend([(dmt.id, dmt.name) for dmt in DiseaseManagementTeam.objects.all()])

years = Document.objects.distinct().values('publish_year').order_by('-publish_year')

for year in years:
    yr = year['publish_year']
    YEAR.append((yr, yr))
    YEAR_START.append((yr, yr))
    YEAR_END.append((yr, yr))
    


doc_types = Document.objects.distinct().values('document_type').order_by('document_type')
DOC_TYPE = []

for doc_type in doc_types:
    dt = doc_type['document_type']
    count = Document.objects.filter(document_type__exact=dt).count()
    dt_ct = '%s (%s)' % (dt, count)
    DOC_TYPE.append((dt, dt_ct))

IMPACT_FACTOR = (
    ('', ''),
    ('25+', '25+'),
    ('15-25', '15-25'),
    ('10-15', '10-15'),
    ('< 10', '< 10')
    )

EXPORT_CHOICES = (
    ('', ''),
    ('CSV', 'Excel CSV'),
    ('PDF', 'PDF'),
    ('TXT', 'Plain text'),
    ('RIS', 'EndNote or RefWorks (RIS)')
    )


class TabularCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<table><tr>']
        str_values = set([force_unicode(v) for v in value]) # Normalize to strings.
        count = 0
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            count += 1
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(u'<td><label>%s %s</label></td>' % (rendered_cb, escape(force_unicode(option_label))))
            if not count % 4:
                output.append(u'</tr><tr>')
        output.append(u'</tr></table>')
        return u'\n'.join(output)





class BulkLoadForm(forms.Form):
    file_type = forms.CharField(max_length=8, widget=forms.Select(choices=BULK_LOAD_TYPES))
    dmt = forms.IntegerField(widget=forms.Select(choices=DMT), label='Select the DMT', help_text='(for EndNote XML files only)')
    year = forms.CharField(max_length=5, widget=forms.Select(choices=YEAR), label='Select the year', help_text='Leave blank for current year (for Employee files only)')
    bulk_file = forms.FileField(label='Select the file to upload')




class AdvancedSearchForm(forms.Form):
    author = forms.CharField(required=False, help_text='Separate multiple authors with a semi-colon', widget=forms.TextInput(attrs={'autocomplete':'off', 'title':'MSKCC authors'}))
    keywords = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off', 'title':'Searches article title, abstract and article keywords'}))
    journal = forms.CharField(required=False, label='Source', help_text='Enter Journal or Book Title', widget=forms.TextInput(attrs={'autocomplete':'off', 'title':'Includes titles of journals, books, and book series'}))
    
    dmt = forms.ChoiceField(choices=DMT, label='DMT', required=False, widget=forms.Select(attrs={'title':'MSK Disease Management Teams'}))
    
    
    year_start = forms.ChoiceField(choices=YEAR, label='Year published', help_text='begin', required=False)
    year_end = forms.ChoiceField(choices=YEAR, label='to', help_text='end', required=False)
    ## commented out until impact factor import is written
#     impact_factor = forms.ChoiceField(choices=IMPACT_FACTOR, label='Journal impact factor', required=False)
    doc_type = forms.MultipleChoiceField(choices=DOC_TYPE, widget=TabularCheckboxSelectMultiple(choices=DOC_TYPE, attrs={'class':'inner'}), label='Document type', required=False)




class ExportForm(forms.Form):
    previous_uri = forms.CharField(widget=forms.HiddenInput, required=True)
    format = forms.ChoiceField(choices=EXPORT_CHOICES, label='Export as:', required=True)



class CommentForm(forms.Form):
    address = forms.EmailField(label='Email Address')
    name = forms.CharField(label='Name')
    comment = forms.CharField(label='Comments', widget=forms.Textarea)





