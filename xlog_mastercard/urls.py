from django.urls import path
from . import views

app_name = 'xlog_mastercard'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('download_filtered_by_de032/', views.download_filtered_by_de032, name='download_filtered_by_de032'),
]
