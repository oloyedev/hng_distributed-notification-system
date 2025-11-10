from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.CreateUserView.as_view(), name="create_user"),
    path("login", views.LoginUserView.as_view(), name="login_user"),
    path("update-push-token/", views.PushTokenUpdateView.as_view(), name="push_token_update"),
    path("get-details/", views.UserDetail.as_view(), name="user_details"),
    path("refresh-token/", views.TokenRefreshView.as_view(), name="token_refresh"),
]
