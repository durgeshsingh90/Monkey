from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_log/', views.upload_log, name='upload_log'),
]
