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




from django.db import models
import datetime

from library.synapse.util import remove_punctuation, is_number_normalize


class Announcement(models.Model):
    title = models.CharField(max_length=300, db_index=True)
    body = models.TextField()
    pub_date = models.DateTimeField(editable=False)
    create_date = models.DateTimeField(editable=False, default=datetime.datetime.now)
    show = models.BooleanField()
    
    class Meta:
        get_latest_by = "pub_date"
        ordering = ['-pub_date', 'title']
        
#     class Admin:
#         date_hierarchy = 'pub_date'
#         list_display = ['title', 'pub_date']
#         list_filter = ['pub_date', 'create_date', 'show']
#         search_fields = ['title', 'body']
        
    def __unicode__(self):
        return u'%s %s' % (self.pub_date, self.title)
        
    def save(self, force_insert=False, force_update=False):
        self.pub_date = datetime.datetime.now()
        super(Announcement, self).save(force_insert, force_update)


class Employee(models.Model):
    emp_id = models.CharField('Employee ID', max_length=10, blank=True, db_index=True) #, unique=True)
    first_name = models.CharField(max_length=40, db_index=True)
    middle_name = models.CharField(max_length=40, blank=True, db_index=True)
    last_name = models.CharField(max_length=40, db_index=True)
    job_title = models.CharField(max_length=60, blank=True)
    photo = models.ImageField(upload_to='photos', null=True, blank=True)
    currently_employed = models.BooleanField(default=True)
    
#     class Admin:
#         list_display = ('last_name', 'first_name', 'middle_name', 'emp_id', 'job_title')
#         list_filter = ['currently_employed', 'job_title']
#         search_fields = ['last_name', 'first_name', 'middle_name', 'emp_id']
        
    class Meta:
        ordering = ['last_name', 'first_name', 'middle_name', 'emp_id']
    
    def __unicode__(self):
        return u'%s %s %s' % (self.first_name, self.middle_name, self.last_name)
        
#     def get_absolute_url(self):
#         return "/employee/%s" % self.emp_id


        
class Grant(models.Model):
    name = models.CharField(max_length=250, db_index=True)
    amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    employees = models.ManyToManyField(Employee)


    
class Department(models.Model):
    name = models.CharField(max_length=250, db_index=True)
    cost_center = models.CharField(max_length=5, blank=True, db_index=True) #, unique=True)
#     short_name = models.SlugField(prepopulate_from=(("name"),), db_index=True)
    
    def __unicode__(self):
        return u'%s' % self.name
    
    class Admin:
        list_display = ['name', 'cost_center']
        search_fields = ['name', 'cost_center']
        
    class Meta:
        ordering = ['name']


    
class EmployeeDepartment(models.Model):
    year_begin = models.IntegerField(max_length=4, null=True, blank=True)
    year_end = models.IntegerField(max_length=4, null=True, blank=True)
    employee = models.ForeignKey(Employee)
    department = models.ForeignKey(Department)
    
#     class Admin:
#         list_display = ('employee', 'department', 'year_begin', 'year_end')
#         list_filter = ['department']
#         search_fields = ['employee__last_name']
        
    class Meta:
        ordering = ['employee', 'department', '-year_begin']


    
class Institution(models.Model):
    name = models.CharField(max_length=150, db_index=True)
#     short_name = models.SlugField(prepopulate_from=(("name"),), db_index=True, core=True)
    
    def __unicode__(self):
        return u'%s' % self.name
    
#     class Admin:
#         pass


    
class DiseaseManagementTeam(models.Model):
    name = models.CharField('Disease Management Team', max_length=250, db_index=True)
    
    def __unicode__(self):
        return u'%s' % self.name
    
#     class Admin:
#         pass
        
    class Meta:
        ordering = ['name']


       
class Document(models.Model):
    title = models.CharField(max_length=500, db_index=True)
    stripped_title = models.CharField(max_length=500, db_index=True, blank=True)
#     short_title = models.SlugField(prepopulate_from=(("title",)), blank=True, db_index=True)
    doi = models.CharField('Digital Object Identifier', max_length=300, blank=True, db_index=True) #, unique=True)
    abstract = models.TextField(blank=True)
    author_names = models.CharField(max_length=6200, db_index=True)
    stripped_author_names = models.CharField(max_length=2500, db_index=True, blank=True)
    affiliations = models.TextField(blank=True)
    volume = models.CharField(max_length=20, blank=True)
    issue = models.CharField(max_length=40, blank=True)
    page_range = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, blank=True)
    publish_date = models.CharField(max_length=40, blank=True)
    publish_year = models.IntegerField(max_length=4, null=True, blank=True)
    document_type = models.CharField(max_length=80, blank=True)
    document_subtype = models.CharField(max_length=40, blank=True)
    source = models.ForeignKey('Source', null=True, blank=True)
    dmt = models.ForeignKey(DiseaseManagementTeam, null=True, blank=True, db_index=True)
    mod_date = models.DateTimeField(editable=False)
    create_date = models.DateTimeField(editable=False, default=datetime.datetime.now)

    
    def __unicode__(self):
        return u'Title: %s  Authors: %s' % (self.title, self.author_names)
        
    def spage(self):
        return self.page_range.split('-')[0]
        
    def fixed_is_number(self):
        """
        Returns the is_number field padded with zeroes prepended to 8 characters.
        
        If the ISSN/ISBN is less than 8 characters, it went through an integer chop at some
        point, such that leading zeroes were truncated.  This method returns a properly-padded number,
        with leading zeroes prepended.
        """
        if len(self.source.is_number) < 8:
            return self.source.is_number.rjust(8, '0')
        else:
            return self.source.is_number
            
    def fixed_issue(self):
        if self.issue:
            return self.issue.split()[0]
        else:
            return None
        
    def save(self, force_insert=False, force_update=False):
        if not self.stripped_title:
            self.stripped_title = remove_punctuation(self.title)
        if not self.stripped_author_names:
            self.stripped_author_names = remove_punctuation(self.author_names)
        self.mod_date = datetime.datetime.now()
        super(Document, self).save(force_insert, force_update)
    
    
    class Admin:
        list_display = ['title', 'author_names']
        list_filter = ['document_type', 'dmt', 'publish_year']
        search_fields = ['title', 'author_names']
        
    def get_absolute_url(self):
        return "/document/%i/" % self.id


    
class Keyword(models.Model):
    term = models.CharField(max_length=2800, db_index=True)
    document = models.ForeignKey(Document, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.term


    
class Publisher(models.Model):
    name = models.CharField(max_length=250, db_index=True)
    sources = models.ManyToManyField('Source', null=True, blank=True)
    
#     class Admin:
#         search_fields = ['name', 'sources']
    
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s' % self.name

    
class Source(models.Model):
    IS_TYPE_CHOICES = (
        ('ISSN', 'International Standard Serial Number'),
        ('ISBN', 'International Standard Book Number'),
        ('ESSN', 'International Standard Electronic Serial Number')
    )
    name = models.CharField(max_length=250, db_index=True)
    publication_type = models.CharField(max_length=100, db_index=True)
    book_authors = models.CharField(max_length=250, db_index=True, blank=True)
    is_number = models.CharField(max_length=17, db_index=True, blank=True) #, unique=True)
    es_number = models.CharField(max_length=17, db_index=True, blank=True) #, unique=True)
    is_type = models.CharField(max_length=4, choices=IS_TYPE_CHOICES, blank=True)
    
#     class Admin:
#         search_fields = ['name', 'is_number']
#         list_filter = ['is_type', 'publication_type']
        
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return u'%s' % self.name
        
    def save(self, force_insert=False, force_update=False):
        if self.is_number:
            self.is_number = is_number_normalize(self.is_number)
        if self.es_number:
            self.es_number = is_number_normalize(self.es_number)
        super(Source, self).save(force_insert, force_update)

    
class Impact(models.Model):
    value = models.CharField(max_length=20)
    year = models.IntegerField()
    source_id = models.ForeignKey(Source)


class NameOrder(models.Model):
    order = models.CharField(max_length=11)
    
#     class Admin:
#         list_display = ('order', )
        
    def __unicode__(self):
        return u'%s' % self.order
        
        
                
class Publication(models.Model):
    author_name = models.CharField("Author's Name Variation", max_length=150, db_index=True)
    name_order = models.ForeignKey(NameOrder)
    institution = models.ForeignKey(Institution, null=True, blank=True, db_index=True)
    affiliation = models.CharField(max_length=2400, blank=True, db_index=True)
    document = models.ForeignKey(Document, db_index=True)
    author = models.ForeignKey(Employee, null=True, blank=True, db_index=True)
    
#     class Admin:
# #         list_display = ['document', 'author_name']
#         search_fields = ['author_name'] #, 'document__title']
        
    def __unicode__(self):
        return u'Title: %s  Author: %s' % (self.document.title, self.author_name)
    