from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, "base/base.html")

def about(request):
    return HttpResponse('About page')
