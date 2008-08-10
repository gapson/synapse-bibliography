from django.contrib import admin

from library.synapse.models import Announcement, Employee, Grant, Department, EmployeeDepartment, Institution, DiseaseManagementTeam, \
    Document, Keyword, Publisher, Source, Impact, NameOrder, Publication
    
class AnnouncementAdmin(admin.ModelAdmin):
    date_hierarchy = 'pub_date'
    list_display = ('title', 'pub_date')
    list_filter = ('show',)
    search_fields = ('title', 'body')
    
class EmployeeDepartmentInline(admin.TabularInline):
    date_hierarchy = ('year_end', 'year_begin')
    model = EmployeeDepartment
    extra = 1
    verbose_name = "Employee's Department"
    verbose_name_plural = "Employee's Departments"
#     list_display = ('employee', 'department', 'year_begin', 'year_end')
#     list_filter = ['department']
#     search_fields = ['employee__last_name']
    
class EmployeeAdmin(admin.ModelAdmin):
    inlines = (EmployeeDepartmentInline, )
    list_display = ('last_name', 'first_name', 'middle_name', 'emp_id', 'job_title')
    list_display_links = ('last_name', 'first_name')
    list_filter = ('currently_employed', 'job_title')
    search_fields = ('last_name', 'first_name', '=emp_id')
    
# class GrantAdmin(admin.ModelAdmin):
#     pass
    
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost_center')
    list_display_links = ('name', 'cost_center')
    search_fields = ('name', '=cost_center')

    
class InstitutionAdmin(admin.ModelAdmin):
    pass
    
class DiseaseManagementTeamAdmin(admin.ModelAdmin):
    pass
    
class PublicationInline(admin.TabularInline):
    model = Publication
    extra = 1
    search_fields = ('author_name', )

class KeywordInline(admin.TabularInline):
    model = Keyword
    extra = 10
    
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_names')
    list_filter = ('document_type', 'dmt', 'publish_year')
    search_fields = ('title', 'author_names')
    inlines = (PublicationInline, KeywordInline, )
    fieldsets = (
        (None, {
            'fields': ('title', 'author_names', 'affiliations', 'abstract'),
            'classes': ('wide', )
            }
        ),
        ('Citation', {
            'classes': ('extrapretty', ),
            'fields': ('source', 'volume', 'issue', 'page_range', 'publish_date', 'publish_year', 'language', 'doi')
            }
        ),
        ('Document type', {
            'classes': ('collapse', 'extrapretty'),
            'fields': ('document_type', 'document_subtype')
            }
        ),
        ('Comparison', {
            'classes': ('collapse', 'wide', ),
            'fields': ('stripped_title', 'stripped_author_names')
            }
        )
    )
    
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ('name', 'sources')
    
class SourceAdmin(admin.ModelAdmin):
    search_fields = ('name', 'is_number')
    list_filter = ('is_type', 'publication_type')
    
# class ImpactAdmin(admin.ModelAdmin):
#     pass
    
class NameOrderAdmin(admin.ModelAdmin):
    list_display = ('order', )
    
    
#######################
##  Registration
#######################

admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Employee, EmployeeAdmin)
# admin.site.register(Grant, GrantAdmin)
admin.site.register(Department, DepartmentAdmin)
# admin.site.register(EmployeeDepartment, EmployeeDepartmentInline)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(DiseaseManagementTeam, DiseaseManagementTeamAdmin)
admin.site.register(Document, DocumentAdmin)
# admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Source, SourceAdmin)
# admin.site.register(Impact, ImpactAdmin)
admin.site.register(NameOrder, NameOrderAdmin)
# admin.site.register(Publication, PublicationAdmin)