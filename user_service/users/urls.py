from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.CreateUserView.as_view(), name="create_user"),
    path("login", views.LoginUserView.as_view(), name="login_user"),
    #path("get-details/")
]
