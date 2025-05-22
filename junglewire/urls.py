from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin.html', views.admin, name='admin'),
        path('schedule/', views.api_schedule, name='api_schedule'),
    path('save_testcases/', views.save_testcases_api, name='save_testcases_api'),
path('load_testcase/<str:name>/', views.load_testcase_file, name='load_testcase'),


    ]