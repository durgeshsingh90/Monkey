from django.urls import path
from .views import index, get_content, generate_output

urlpatterns = [
    path('', index, name='index'),
    path('get_content/', get_content, name='get_content'),
    path('generate_output/', generate_output, name='generate_output'),  # ✅ This is correct
]
