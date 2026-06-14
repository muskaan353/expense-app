from django.contrib import admin

from apps.imports.models import ImportIssue, ImportRow, ImportSession


admin.site.register(ImportSession)
admin.site.register(ImportRow)
admin.site.register(ImportIssue)
