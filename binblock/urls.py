from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_content/', views.get_content, name='get_content'),
]
