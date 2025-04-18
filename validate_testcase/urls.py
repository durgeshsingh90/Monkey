from django.urls import path
from .views import validate_testcase_view

urlpatterns = [
    path('', validate_testcase_view, name='validate_testcase'),
]
