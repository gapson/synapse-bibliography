from django.conf.urls.defaults import *

from library.synapse.feeds import LatestDocuments, LatestDocumentsByAuthor, LatestDocumentsByDocType

feeds = {
    'latest': LatestDocuments,
    'author': LatestDocumentsByAuthor,
    'doctype': LatestDocumentsByDocType,
    }

urlpatterns = patterns('',
    # Example:
    # (r'^library/', include('library.foo.urls')),

    # Uncomment this for admin:
     (r'^admin/', include('django.contrib.admin.urls')),
     
     (r'^bulkload/$', 'library.synapse.views.bulk_upload'),
     (r'^duplicates/$', 'library.synapse.views.duplicates'),
     (r'^$', 'library.synapse.views.search_form'),
     (r'^dmt/$', 'library.synapse.views.search_dmt_form'),
     (r'^accounts/login/$', 'django.contrib.auth.views.login'),
     (r'^ac/authors/$', 'library.synapse.views.autocomplete_authors'),
     (r'^ac/sources/$', 'library.synapse.views.autocomplete_sources'),
     (r'^documents/search/$', 'library.synapse.views.search'),
     (r'^export/(?P<format>\w+)/$', 'library.synapse.views.export'),
     (r'^document/(?P<document_id>\d+)/$', 'library.synapse.views.full_document'),
     (r'^comments/$', 'library.synapse.views.comments'),
     (r'^comments/thanks/$', 'library.synapse.views.comments_thanks'),
     (r'^managing_your_refs/$', 'library.synapse.views.myr'),
     (r'^pub_ranking_tools/$', 'library.synapse.views.prt'),
     (r'^what_is_synapse/$', 'library.synapse.views.wis'),
     (r'^newsfeeds/$', 'library.synapse.views.newsfeeds'),
     (r'^newsfeeds/search/$', 'library.synapse.views.newsfeeds_search'),
     
     (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
#      (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/Users/herndonp/Projects/Work/django/library/media'} ),
     (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/Users/herndonp/Projects/Work/django/googlesvn/synapse-bibliography/library/media'} ),
)
