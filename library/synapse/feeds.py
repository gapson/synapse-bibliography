from django.contrib.syndication.feeds import Feed
from library.synapse.models import Document, Employee, Publication

from datetime import date

class LatestDocuments(Feed):
    title = "Synapse Recently Added Documents"
    link = "/"
    description = "Updates on additions to Synapse"
    
    def items(self):
        today = date.today()
        week_ago = date.fromordinal(today.toordinal() - 7)
        
        # TODO: change from last 20 slice to filter(create_date__>=(today - 7 days))
        return Document.objects.filter(create_date__range=(week_ago, today)).order_by('-create_date')
#         return Document.objects.order_by('-create_date')[:20]
        
class LatestDocumentsByAuthor(Feed):
    def get_object(self, author):
    # Should return the author specified
        if len(author) < 1:
            raise ObjectDoesNotExist
        return Employee.objects.filter(id__in=author)
        
    def generate_plural_titles(self, title, obj):
        plural = "s"
        author_names = []
        for emp in obj:
            author_names.append(' '.join((emp.first_name, emp.last_name)))
        if len(author_names) == 1:
            title = ' '.join((title, author_names[0]))
        elif len(author_names) > 1:
            title = title + 's '
            title = title + ' or '.join((', '.join(author_names[:-1]), author_names[-1]))
        return title
        
    def title(self, obj):
        base_title = "Synapse:  Documents written by author"
        title = self.generate_plural_titles(base_title, obj)
        return title
        
    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        id_list = [str(emp.id) for emp in obj]
        feed_base = "/feeds/author/"
        feed_link = '/'.join((feed_base, '/'.join(id_list)))
        return feed_link
        
    def description(self, obj):
        base_title = "Documents written by author"
        title = self.generate_plural_titles(base_title, obj)
        return title
        
    def items(self, obj):
        # Should return the Document objects whose Publications match the author_id
        author_pubs = Publication.objects.filter(author__in=obj)
        return Document.objects.filter(publication__in=author_pubs).order_by('-create_date')

class LatestDocumentsByDocType(Feed):
    def get_object(self, doctype):
        if len(doctype) != 1:
            raise ObjectDoesNotExist
        # Need to parse the doctype, turn it into matching
        dt = doctype[0]
        doc_type = []
        exclude = ('in', 'of', 'a', 'an', 'the', 'in', 'for')
        # Replace with algorithmic parser
        for word in dt.split('_'):
            if word in exclude:
                doc_type.append(word)
            else:
                doc_type.append(word.capitalize())
                
        doc_type = ' '.join(doc_type)
        
#         if dt == 'article':
#             doc_type = 'Article'
#         elif dt == 'conference_paper':
#             doc_type = 'Conference Paper'
#         elif dt == 'review_article':
#             doc_type = 'Review Article'
#         elif dt == 'short_survey':
#             doc_type = 'Short Survey'
#         elif dt == 'editorial':
#             doc_type = 'Editorial'
#         elif dt == 'other':
#             doc_type = 'Other'
#         elif dt == 'book_chapter':
#             doc_type = 'Book Chapter'
#         elif dt == 'book':
#             doc_type = 'Book'
#         elif dt == 'article_in_press':
#             doc_type = 'Article in Press'
#         elif dt == 'unspecified':
#             doc_type = 'Unspecified'
            
        if not doc_type:
            raise ObjectDoesNotExist
        return (dt, doc_type)

    def title(self, obj):
        return "Synapse:  Documents of type %s" % obj[1]
        
    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return "/feeds/doctype/%s/" % obj[0]
        
    def description(self, obj):
        return "Documents of type %s" % obj[1]
        
    def items(self, obj):
        
        return Document.objects.filter(document_type__exact=obj[1]).order_by('-create_date')[:20]