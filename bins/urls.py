from django.urls import path
from bins import views

app_name = 'bins'

urlpatterns = [
    path("create_bin/", views.create_bin, name="index"),
    path("search/", views.create_bin, name="search"),
    path("view_bin/<str:hash>", views.view_bin, name="view_bin"),
    path("user_bins/", views.user_bins, name="user_bins"),
    path("user_comments/", views.user_comments, name="user_comments"),
    path("bin_likes_dislikes/<str:hash>/", views.likes_dislikes_bins, name="bin_likes_dislikes"),
    path("bin_comment/<str:hash>/", views.bin_comment, name="bin_comment"),
    path("edit_bin/<str:hash>/", views.edit_bin, name="edit_bin"),
    path("delete_bin/<str:hash>/", views.delete_bin, name="delete_bin"),
]
