"""Pagination contracts shared by current and historical APIs."""
from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PatientPagination(PageNumberPagination):
    page_size = 10


class ClinicalPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        self.page_size = settings.CLINICAL_PAGE_SIZE
        self.max_page_size = settings.CLINICAL_MAX_PAGE_SIZE
        return super().get_page_size(request)
