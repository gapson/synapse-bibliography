### Not part of Synapse, django-snippet 867
# http://www.djangosnippets.org/snippets/867/


from django.core.paginator import QuerySetPaginator, InvalidPage

__all__ = ('BetterQuerySetPaginator', 'InvalidPage')

class BetterQuerySetPaginator(QuerySetPaginator):
    """
    An enhanced version of the QuerySetPaginator.
    
    >>> my_objects = BetterQuerySetPaginator(queryset, 25)
    >>> page = 1
    >>> context = {
    >>>     'my_objects': my_objects.get_context(page),
    >>> }
    """
    def get_context(self, page, range_gap=5):
        try:
            page = int(page)
        except (ValueError, TypeError), exc:
            raise InvalidPage, exc
        
        if page > 5:
            start = page-range_gap
        else:
            start = 1

        if page < self.num_pages-range_gap:
            end = page+range_gap+1
        else:
            end = self.num_pages+1

        paginator = self.page(page)

        context = {
            'page_range': range(start, end),
            'objects': paginator.object_list,
            'num_pages': self.num_pages,
            'page': page,
            'has_previous': paginator.has_previous(),
            'has_next': paginator.has_next(),
            'previous_page': paginator.previous_page_number(),
            'next_page': paginator.next_page_number(),
            'is_first': page == 1,
            'is_last': page == self.num_pages,
        }
        
        return context