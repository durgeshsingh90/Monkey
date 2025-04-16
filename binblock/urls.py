from django.urls import path
from .views import bin_blocking_editor

app_name = 'binblock'

urlpatterns = [
    path('', bin_blocking_editor, name='binblocking_editor'),
]
