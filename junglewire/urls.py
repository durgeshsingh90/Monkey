from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin.html', views.admin, name='admin'),
        path('schedule/', views.api_schedule, name='api_schedule'),
    path('save_testcases/', views.save_testcases_api, name='save_testcases_api'),
    path('load_testcase/<str:name>/', views.load_testcase_file, name='load_testcase'),
path('delete_testcases/', views.delete_testcases, name='delete_testcases'),
path('create_testcase_file/', views.create_testcase_file, name='create_testcase_file'),
path('upload_testcase_file/', views.upload_testcase_file, name='upload_testcase_file'),
path('list_testcase_files/', views.list_testcase_files, name='list_testcase_files'),
path('save_testcases/<str:filename>/', views.save_testcases_file, name='save_testcases_file'),

    ]