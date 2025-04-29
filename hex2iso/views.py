# Create your views here.
from django.shortcuts import render

def index(request):
    return render(request, 'hex2iso/index.html')
