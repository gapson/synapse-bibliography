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


from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import *
from django.shortcuts import get_object_or_404, render_to_response
from django.template import Context
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.newforms.widgets import flatatt
from django.core.mail import send_mail, BadHeaderError
from django.core.paginator import ObjectPaginator, InvalidPage


from rest import RESTView
from util import BulkParserDispatcher
from search import search_all

from library.synapse.models import DiseaseManagementTeam, Document, Publication, Source, Keyword, Employee, Announcement
from library.synapse.forms import BulkLoadForm, AdvancedSearchForm, ExportForm, DMT, CommentForm
from library.synapse import exporters

import iplib


def is_internal(request):
    if not request.META.has_key('REMOTE_ADDR'):
        return False
    else:
        main = iplib.CIDR('140.163.0.0/16')
        zrc = iplib.CIDR('172.16.0.0/12')
        vpn = iplib.CIDR('192.168.0.0/16')
        addr = request.META['REMOTE_ADDR']
        
        if main.is_valid_ip(addr) or zrc.is_valid_ip(addr) or vpn.is_valid_ip(addr):
            return True
        else:
            return False


@staff_member_required        
def bulk_upload(request):
    if request.method == 'POST':
        form = BulkLoadForm(request.POST, request.FILES)
        if form.is_valid():
            file_type = form.cleaned_data['file_type']
            year = form.cleaned_data['year']
            dmt = form.cleaned_data['dmt']
            content = request.FILES['bulk_file']['content']
            # parser is a file parser instance of appropriate type that's been passed the content
            dispatcher = BulkParserDispatcher(file_type, content, year, dmt)
            status = dispatcher.parser.parse()
            return render_to_response('synapse/duplicates.html', Context({'status':status, 'is_internal':is_internal(request)}))
    else:
        form = BulkLoadForm()
    return render_to_response('synapse/bulkupload.html', {'form': form, 'is_internal':is_internal(request)})
    
def duplicates(request):
    return render_to_response('synapse/duplicates.html', {'file_type': 'nothing at this time',
                                'file_text': 'no file text either'})
                                

# @login_required    
def search(request):
    if request.GET.has_key('format') and request.GET['format']:
        ref = request.META['HTTP_REFERER']
        start = ref.index('?')
        q_string = ref[start:]
        target = "/export/" + request.GET['format'] + "/" + q_string
        return HttpResponseRedirect(target)


    else:
        form = AdvancedSearchForm(request.GET)
        if form.is_valid():
            do_search = False
            for item in form.cleaned_data.values():
                if item:
                    do_search = True
            if do_search:
                results = search_all(form.cleaned_data)
                result_count = len(results)
                
                search_phrase = []
                if form.cleaned_data['author'] and not form.cleaned_data['author'] == 'Last Name, First':
                    author = form.cleaned_data['author'].strip().strip(';')
                    search_phrase.append(author)
                
                if form.cleaned_data['journal'] and not form.cleaned_data['journal'] == 'Ex: Blood':
                    search_phrase.append(form.cleaned_data['journal'])
                    
                if form.cleaned_data['keywords'] and not form.cleaned_data['keywords'] == 'Ex: melanoma':
                    search_phrase.append(form.cleaned_data['keywords'])
                    
                if form.cleaned_data['dmt'] and not form.cleaned_data['dmt'] == '0':
                    for dmt_id, name in DMT:
                        if dmt_id == int(form.cleaned_data['dmt']):
                            search_phrase.append(' '.join(('DMT:',name)))
                    
                if form.cleaned_data['doc_type']:
                    search_phrase.extend(form.cleaned_data['doc_type'])
                
                if form.cleaned_data['year_start'] and not form.cleaned_data['year_start'] == 'BLANK':
                    search_phrase.append('From %s' % form.cleaned_data['year_start'])

                if form.cleaned_data['year_end'] and not form.cleaned_data['year_end'] == 'BLANK':
                    search_phrase.append('To %s' % form.cleaned_data['year_end'])
                    
                search_phrase = ' and '.join(search_phrase)
                
                paginator = ObjectPaginator(results, 200)
                
                page = 1
                if request.GET.has_key('page'):
                    page = int(request.GET['page'])
                if page > 0:
                    results_page = paginator.get_page(page - 1)
                
                previous = 0
                next = 1
                if page > 0:
                    previous = page - 1
                next = page + 1
                
                page_offset = 0
                if page > 1:
                    page_offset = previous * 200
                    
                full_uri = "/documents/search/?"

                full_uri = full_uri + request.GET.urlencode()
                return render_to_response('synapse/results.html', Context({'data': search_phrase,
                                                                          'publications': results_page,
                                                                          'page': page,
                                                                          'pages': paginator.pages,
                                                                          'page_range': paginator.page_range,
                                                                          'has_next': paginator.has_next_page(previous),
                                                                          'has_previous': paginator.has_previous_page(previous),
                                                                          'next': next,
                                                                          'previous': previous,
                                                                          'page_offset': page_offset,
                                                                          'uri': full_uri,
                                                                          'result_count': result_count,
                                                                          'is_internal': is_internal(request)}))
            else:
                form = AdvancedSearchForm()
                return render_to_response('synapse/search.html', {'form': form, 'show_dmt': False, 'is_internal': is_internal(request)})


# @login_required
def search_form(request):
    form = AdvancedSearchForm()
    announcement = None
    try:
        announcement = Announcement.objects.filter(show__exact=True).latest()
    except Announcement.DoesNotExist:
        pass
    return render_to_response('synapse/search.html', {'form': form, 'announcement': announcement, 'show_dmt': False, 'is_internal': is_internal(request)})

# @login_required
def search_dmt_form(request):
    form = AdvancedSearchForm()
    announcement = None
    try:
        announcement = Announcement.objects.filter(show__exact=True).latest()
    except Announcement.DoesNotExist:
        pass
    return render_to_response('synapse/search.html', {'form': form, 'announcement': announcement, 'show_dmt': True, 'is_internal': is_internal(request)})


# @login_required
def export(request, format=None, kwargs=None):
    if request.method == 'GET':
        results = None
        exporter = None
        form = AdvancedSearchForm(request.GET)
        if form.is_valid():
            do_search = False
            for item in form.cleaned_data.values():
                if item:
                    do_search = True
            if do_search:
#                 print form.cleaned_data['doc_type']
#                 print type(form.cleaned_data['doc_type'])
                results = search_all(form.cleaned_data)
        else:
            return HttpResponseRedirect('/')

        if format:
            try:
                exporter = getattr(exporters, format)
            except AttributeError:
                raise Http404('No export format %s is available.' % format)
                
        if results:
            response = exporter(results)
            return response
        else:
            return HttpResponseRedirect('/')
            
# @login_required
def comments(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            subject = '[Synapse] Comment or Correction from %s' % form.cleaned_data['name']
            comment = form.cleaned_data['comment']
            address = form.cleaned_data['address']
            try:
                send_mail(subject, comment, address, ['zzPDL_MIS_Synapse@mskcc.org', 'herndonp@mskcc.org'])
            except BadHeaderError:
                return render_to_reponse('synapse/comments.html', {'form': form, 'msg':'Invalid header found.', 'is_internal': is_internal(request)})
            return HttpResponseRedirect('/comments/thanks/')
        else:
            return render_to_response('synapse/comments.html', {'form': form, 'msg':'Please enter all fields correctly.', 'is_internal': is_internal(request)})
    else:
        form = CommentForm()
        return render_to_response('synapse/comments.html', {'form': form, 'is_internal': is_internal(request)})
        
# @login_required
def comments_thanks(request):
    msg = 'Thanks for your interest.  A library staff member will address your concerns as soon as possible.'
    return render_to_response('synapse/comments.html', {'msg':msg, 'is_internal': is_internal(request)})

# @login_required
def autocomplete_authors(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s\n' % r #'%s\n' % (r['author_name'])
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 25)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    author_ids = Publication.objects.filter(author__isnull=False).distinct().values('author')
    author_ids = [x['author'] for x in author_ids]
    
    
    employees = Employee.objects.filter(id__in=author_ids).filter(last_name__istartswith=q).order_by('last_name', 'first_name').values('last_name', 'first_name')[:limit]
    authors = [', '.join((employee['last_name'], employee['first_name'])) for employee in employees]

    return HttpResponse(iter_results(authors), mimetype='text/plain')
    
# @login_required
def autocomplete_sources(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s\n' % (r['name'])
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 25)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    sources = Source.objects.values('name').filter(name__istartswith=q).distinct()[:limit]
    return HttpResponse(iter_results(sources), mimetype='text/plain')


# @login_required
def full_document(request, document_id):
    doc = get_object_or_404(Document, pk=document_id)
    return render_to_response('synapse/document.html', {'doc': doc})


# @login_required
def myr(request):
    return render_to_response('synapse/managing_your_refs.html', {'is_internal': is_internal(request)})
    
# @login_required
def prt(request):
    return render_to_response('synapse/pub_ranking_tools.html', {'is_internal': is_internal(request)})
    
# @login_required
def wis(request):
    addr = request.META['REMOTE_ADDR']
    return render_to_response('synapse/what_is_synapse.html', {'is_internal': is_internal(request)})