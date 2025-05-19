from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin.html', views.admin, name='admin'),
        path('api/schedule/', views.api_schedule, name='api_schedule'),
path('api/save_testcases/', views.save_testcases_api, name='save_testcases_api'),


    ]