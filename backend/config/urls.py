from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Django admin.
    # Final URL: /admin/
    path("admin/", admin.site.urls),

    # API entry point.
    # Everything inside config.api.urls
    # will be available under /api/v1/.
    path(
        "api/v1/",
        include("config.api.urls"),
    ),
]