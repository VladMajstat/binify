from django.urls import path
from users import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("registration/", views.RegistrationView.as_view(), name="registration"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("logout/", views.logout, name="logout"),
    path("password_change/", views.PasswordChangeView.as_view(), name="password_change"),
]
