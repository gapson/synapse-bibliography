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
# from django.newforms.widgets import flatatt
from django.forms.widgets import flatatt
from django.core.mail import send_mail, BadHeaderError
from django.core.paginator import InvalidPage
from django.core.paginator import QuerySetPaginator
from django.db.models import Q

from rest import RESTView
from util import BulkParserDispatcher
from search import search_all

from library.synapse.models import DiseaseManagementTeam, Document, Publication, Source, Keyword, Employee, Announcement
from library.synapse.forms import BulkLoadForm, AdvancedSearchForm, ExportForm, DMT, CommentForm, NewsfeedSearchForm
from library.synapse import exporters, paginator

from urllib import urlencode

# only external dependency
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
#             content = request.FILES['bulk_file']['content']
            content = request.FILES['bulk_file'].read()
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
                                
def build_search_phrase(form):
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
    return search_phrase
    
def newsfeeds(request):
    form = NewsfeedSearchForm()
    return render_to_response('synapse/feeds.html', {'is_internal': is_internal(request), 'form': form})
    
def newsfeeds_search(request):
    form = NewsfeedSearchForm(request.POST)
    if form.is_valid():
        if form.cleaned_data['author'] != 'Last Name, First':
            q_list = []
            authors = form.cleaned_data['author'].rstrip('; ').split('; ')
            results = Employee.objects.all()
            for author in authors:
                if author:
                    lname, fname = author.split(', ')
                    q_list.append(Q(last_name__iexact=lname, first_name__iexact=fname))
            results = Employee.objects.filter(q_list[0])
            for q in q_list[0:]:
                results = results | Employee.objects.filter(q)
                
            combined_url = ''
            if results.count() > 1:
                ids = [str(emp.id) for emp in results]
                
                combined_url = '/'.join(ids)
                
            return render_to_response('synapse/feeds.html', {'is_internal': is_internal(request), 'form': form, 'results': results, 'combined_url': combined_url})
        else:
            return HttpResponseRedirect('/newsfeeds/')
    else:
        return HttpResponseRedirect('/newsfeeds/')
    
                

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
            msg = None
            do_search = False
            for item in form.cleaned_data.values():
                if item and item not in ['Last Name, First', 'Ex: Blood', 'Ex: melanoma', '0', 'BLANK']:
                    do_search = True
            if do_search:
                # results is a QuerySet
                results = search_all(form.cleaned_data)
#                 print results
                result_count = len(results)
#                 print result_count

                search_phrase = build_search_phrase(form)
                
                if results:
                    paginator = QuerySetPaginator(results, 200)
                    # print paginator
                    
                    try:
                        result_count = paginator.count
                        # print "Result Count: ", result_count
                    except TypeError:
    #                     result_count = 0
                        msg = u'Your search for <em>%s</em> returned no results.  Please broaden your search and try again.' % search_phrase
                        form = AdvancedSearchForm()
                        return render_to_response('synapse/search.html', {'form': form, 'show_dmt': False, 'is_internal': is_internal(request), 'msg':msg })
                        
                    
                    
                        
#                     full_uri = "/documents/search/?"
#     
#                     full_uri = full_uri + request.GET.urlencode()
#                     full_uri = request.path + '?' + request.GET.urlencode()
                    # TODO: rip request.GET apart, rebuild new URL without the extraneous page terms
                    new_url = {}
                    if request.GET.has_key('author'):
                        if request.GET['author'] != 'Last Name, First':
                            new_url['author'] = request.GET['author']
                            
                    if request.GET.has_key('journal'):
                        if request.GET['journal'] != '':
                            new_url['journal'] = request.GET['journal']
                            
                    if request.GET.has_key('year_start'):
                        if request.GET['year_start'] != 'BLANK':
                            new_url['year_start'] = request.GET['year_start']
                            
                    if request.GET.has_key('year_end'):
                        if request.GET['year_end'] != 'BLANK':
                            new_url['year_end'] = request.GET['year_end']
                            
                    if request.GET.has_key('keywords'):
                        if request.GET['keywords'] != '':
                            new_url['keywords'] = request.GET['keywords']
                        
                    if request.GET.has_key('doc_type'):
                        new_url['doc_type'] = form.cleaned_data['doc_type']
                        
                    
                    
                    results_page = None
                    page = 0
                    if request.GET.has_key('page'):
                        page = int(request.GET['page'])
                    else:
                        page = 1
                        
                    results_page = paginator.page(page)
                        
                    previous = 0
                    next = 0
                    if page > 0:
                        previous = results_page.number - 1
                    next = results_page.number + 1
                    
#                     if request.GET.has_key('page'):
#                         if request.GET['page'] != '':
#                             new_url['page'] = request.GET['page']

#                     print "new_url: ", urlencode(new_url, doseq=True)
                    
                    full_uri = '?' + urlencode(new_url, doseq=True)

                    
                    context = {
                            'data': search_phrase,
                            'publications': results_page.object_list,
                            'pages': paginator.num_pages,
                            'page_range':paginator.page_range,
                            'page': results_page.number,
                            'has_next':results_page.has_next(),
                            'has_previous':results_page.has_previous(),
                            'next':next,
                            'previous':previous,
                            'uri':full_uri,
                            'result_count':paginator.count,
                            'is_internal': is_internal(request),
                            }
                    return render_to_response('synapse/results.html', context)
                else:
                    msg = u'Your search for <em>%s</em> returned no results.  Please broaden your search and try again.' % search_phrase
                    form = AdvancedSearchForm()
                    return render_to_response('synapse/search.html', {'form': form, 'show_dmt': False, 'is_internal': is_internal(request), 'msg':msg })

            else:
                msg = u'Please enter at least one search term.'
                form = AdvancedSearchForm()
                return render_to_response('synapse/search.html', {'form': form, 'show_dmt': False, 'is_internal': is_internal(request), 'msg':msg })


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
#     addr = request.META['REMOTE_ADDR']
    return render_to_response('synapse/what_is_synapse.html', {'is_internal': is_internal(request)})