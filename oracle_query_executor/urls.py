from django.urls import path
from . import views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('execute_queries/', views.execute_queries_view),
    path('save_script/', views.save_script_view),
    path('load_scripts/', views.load_scripts_view),
    path('load_history/', views.load_history_view),
    path('save_history/', views.save_history_view),
    path('clear_history/', views.clear_history_view),
]
