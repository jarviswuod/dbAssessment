from django.urls import path
from .views import ExtractDataView, ExtractionJobListView

urlpatterns = [
    path("extract/", ExtractDataView.as_view(), name="extract-data"),
    path("jobs/", ExtractionJobListView.as_view(), name="extraction-jobs"),
]
