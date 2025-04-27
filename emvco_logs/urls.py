from django.urls import path
from . import views

app_name = 'emvco_logs'

urlpatterns = [
    path('', views.index, name='emvco_logs_index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download_filtered_by_de032/', views.download_filtered_by_de032, name='download_filtered_by_de032'),

]
