from django.urls import path
from bins import views

app_name = 'bins'

urlpatterns = [
    path("create_bin/", views.create_bin, name="index"),
    path("view_bin/", views.view_bin, name="view_bin"),
]
