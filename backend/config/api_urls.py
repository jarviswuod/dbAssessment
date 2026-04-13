from django.urls import path, include

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("connections/", include("apps.connections.urls")),
    path("extraction/", include("apps.extraction.urls")),
    path("storage/", include("apps.storage.urls")),
]
