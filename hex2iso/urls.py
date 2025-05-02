from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('convert/', views.convert),             # <== Required!
    path('list_schemas/', views.list_schemas),   # <== Required!
]
