from django.contrib import admin
from .models import ProcessedDataRecord, ExportedFile

admin.site.register(ProcessedDataRecord)
admin.site.register(ExportedFile)
