from django.urls import path
from bins import views
from . import viewsapi

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

    # DRF API endpoints
    path("api/create/", viewsapi.CreateBinAPIView.as_view(), name="api_create_bin"),
    path("api/bin/<int:pk>/", viewsapi.GetBinAPIView.as_view(), name="api_get_bin"),
    path("api/update/<int:pk>/", viewsapi.UpdateBinAPIView.as_view(), name="api_update_bin"),
    path("api/delete/<int:pk>/", viewsapi.DeleteBinAPIView.as_view(), name="api_delete_bin"),

    # Raw content (зручні URL, ставимо перед api/bin/<int:pk>)
    path("api/bin/raw/<int:pk>/", viewsapi.BinRawByPkAPIView.as_view(), name="api_bin_raw_pk"),
    path("api/bin/raw/hash/<str:hash>/", viewsapi.BinRawByHashAPIView.as_view(), name="api_bin_raw_hash"),
    
    # Lists & Search
    path("api/bins/", viewsapi.PublicBinsListAPIView.as_view(), name="api_public_bins"),
    path("api/my-bins/", viewsapi.MyBinsListAPIView.as_view(), name="api_my_bins"),
    path("api/search/", viewsapi.SearchBinsAPIView.as_view(), name="api_search_bins"),
]
