from django.urls import path
from . import views

urlpatterns = [
    path('', views.certifications_index, name='certifications_index'),
    path('get_structure/', views.get_structure, name='get_structure'),
    path('get_testcase_data/', views.get_testcase_data, name='get_testcase_data'),
]
