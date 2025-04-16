from django.urls import path
from .views import merge_pdfs, upload_pdf_ajax

urlpatterns = [
    path('', merge_pdfs, name='merge_pdfs'),
    path('upload-pdf/', upload_pdf_ajax, name='upload_pdf_ajax'),
]
