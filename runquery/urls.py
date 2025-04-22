from django.urls import path
from . import views

urlpatterns = [
        path('', views.query_page, name='query_page'),  # 👈 Loads your main HTML page

    path('execute_oracle_queries/', views.execute_oracle_queries, name='execute_oracle_queries'),
    path('get_oracle_dbs/', views.get_available_oracle_databases, name='get_oracle_dbs'),  # 👈 New
path('get_table_structure/', views.get_table_structure, name='get_table_structure'),
path('pin_table/', views.pin_table, name='pin_table'),
path('unpin_table/', views.unpin_table, name='unpin_table'),


]
