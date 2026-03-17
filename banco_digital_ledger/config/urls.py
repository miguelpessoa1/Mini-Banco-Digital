from django.contrib import admin
from django.urls import path, include
from banco.views import dashboard
from banco.views import dashboard, extrato_conta

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("extrato_conta/<uuid:conta_id>/", extrato_conta, name="extrato_conta"),
]