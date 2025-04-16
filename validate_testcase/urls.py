from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_excel/', views.upload_excel, name='upload_excel'),
    path('upload_logs/', views.upload_logs, name='upload_logs'),
    path('comparison_result/', views.highlight_comparison_results, name='comparison_result'),

]
