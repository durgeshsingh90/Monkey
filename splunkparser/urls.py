# # splunkparser/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.editor_page, name='splunkparser_index'),
    path('settings/', views.config_editor_page, name='splunkparser_settings'),
    path('settings-json/', views.get_settings, name='get_settings_json'),
    path('save-settings/', views.save_settings, name='save_settings_json'),
    path('parse/', views.parse_logs, name='parse_logs'),
    path('clear_output/', views.clear_output_file, name='clear_output_file'),
    path('save_output/', views.save_output_file, name='save_output_file'),
    path('set_default/', views.set_default_values, name='set_default_values'),
    path('validate_output/', views.validate_output, name='validate_output'),  # ✅
    path('load_schema/', views.get_schema, name='load_schema'),   # 👈 New
    path('save_schema/', views.save_schema, name='save_schema'),   # 👈 New
]

