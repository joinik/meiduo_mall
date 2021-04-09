from django.urls import path, register_converter

from apps.users.views import UsernameCountView, RegisterView
from utils.myconverters import UsernameConverter

register_converter(UsernameConverter, 'user')

urlpatterns = [
    path('usernames/<user:username>/count/', UsernameCountView.as_view()),
    path('register/', RegisterView.as_view()),
]
