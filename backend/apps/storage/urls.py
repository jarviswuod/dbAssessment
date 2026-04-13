from django.urls import path
from .views import (
    SubmitDataView,
    ProcessedRecordsView,
    ExportedFilesView,
    DownloadFileView,
    ShareFileView,
)

urlpatterns = [
    path("submit/", SubmitDataView.as_view(), name="submit-data"),
    path("records/", ProcessedRecordsView.as_view(), name="processed-records"),
    path("files/", ExportedFilesView.as_view(), name="exported-files"),
    path("files/<int:file_id>/download/", DownloadFileView.as_view(), name="download-file"),
    path("files/<int:file_id>/share/", ShareFileView.as_view(), name="share-file"),
]
