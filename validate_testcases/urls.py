from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='validate_testcase_home'),
    path('upload_and_compare/', views.upload_and_compare, name='upload_and_compare'),
]
