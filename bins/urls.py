from django.urls import path
from bins import views

app_name = 'bins'

urlpatterns = [
    path("create_bin/", views.create_bin, name="index"),
    path("view_bin/<int:id>", views.view_bin, name="view_bin"),
    path("user_bins/", views.user_bins, name="user_bins"),
    path("bin_likes_dislikes/<int:id>/", views.likes_dislikes_bins, name="bin_likes_dislikes"),
]
