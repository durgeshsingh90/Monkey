from django.urls import path
from . import views

urlpatterns = [
        path('', views.query_page, name='query_page'),  # 👈 Loads your main HTML page

    path('execute_oracle_queries/', views.execute_oracle_queries, name='execute_oracle_queries'),
    path('get_oracle_dbs/', views.get_available_oracle_databases, name='get_oracle_dbs'),  # 👈 New
path('get_table_structure/', views.get_table_structure, name='get_table_structure'),
path('pin_table/', views.pin_table, name='pin_table'),
path('unpin_table/', views.unpin_table, name='unpin_table'),
path("save_history/", views.save_history, name="save_history"),
path("view_history/", views.view_history, name="view_history"),
  path("save_script/", views.save_script),
    path("load_script/", views.load_script),
path("list_scripts/", views.list_scripts, name="list_scripts"),
path("delete_script/", views.delete_script),
path("save_tab_content/", views.save_tab_content),
path("load_tab_content/", views.load_tab_content),
path("start_db_session/", views.start_db_session),
path("get_metadata_columns/", views.get_metadata_columns),

]
