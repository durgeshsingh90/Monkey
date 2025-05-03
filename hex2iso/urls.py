from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='hex2iso_index'),
    path('parse_iso/', views.parse_iso_view, name='parse_iso_view'),
    path('convert/', views.convert_view, name='convert_view'),
    path('list_schemas/', views.list_schemas, name='list_schemas'),
]
