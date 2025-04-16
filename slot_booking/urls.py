from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', views.admin, name='admin'),
    path('config.json', views.config, name='config'),
    path('submit/', views.save_submission, name='submit'),
    path('submissions/', views.get_submissions, name='submissions'), # Used for calendar, booking APIs
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('submissions.json', views.submissions, name='submissionsfile'),  # Used for Monaco editor

]
