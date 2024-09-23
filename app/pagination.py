from rest_framework import pagination
from rest_framework.response import Response
import math



class CustomPagination(pagination.PageNumberPagination):

    limit = 100
    page_size_query_param = 'limit' 
    max_page_size = 1000 

    def get_paginated_response(self, data):

        total_pages = math.ceil(self.page.paginator.count / self.page.paginator.per_page)

        return Response({
            'count': self.page.paginator.count,
            'total_pages': total_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })