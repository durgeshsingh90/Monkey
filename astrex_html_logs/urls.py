from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('upload_log/', views.upload_log),
    path('zip_filtered_files/', views.zip_filtered_files),
    path('download_filtered/', views.download_filtered_by_de032),
    path('convert_emvco/', views.convert_emvco),
 path('admin/', views.admin_config, name='admin_config'),
    path('save_config/', views.save_config, name='save_config'),
    path('load_config/', views.load_config, name='load_config')

]