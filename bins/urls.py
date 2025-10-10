from django.urls import path
from bins import views

app_name = 'bins'

urlpatterns = [
    path("create_bin/", views.CreateBinView.as_view(), name="index"),
    path("view_bin/<str:hash>", views.ViewBin.as_view(), name="view_bin"),
    path("user_bins/", views.UserBinsView.as_view(), name="user_bins"),
    path("user_comments/", views.UserCommentsView.as_view(), name="user_comments"),
    path("bin_likes_dislikes/<str:hash>/", views.BinLikeDislikeView.as_view(), name="bin_likes_dislikes"),
    path("bin_comment/<str:hash>/", views.BinCommentView.as_view(), name="bin_comment"),
    path("edit_bin/<str:hash>/", views.EditBinView.as_view(), name="edit_bin"),
    path("delete_bin/<str:hash>/", views.DeleteBinView.as_view(), name="delete_bin"),
]
