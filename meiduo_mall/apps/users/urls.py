from django.urls import path, register_converter

from apps.users.views import UsernameCountView, RegisterView, MsmCodeView, MobileCountView
from utils.myconverters import UsernameConverter, PhoneConverter

register_converter(UsernameConverter, 'user')
register_converter(PhoneConverter, 'phone')

urlpatterns = [
    path('usernames/<user:username>/count/', UsernameCountView.as_view()),
    path('mobiles/<phone:mobile>/count/', MobileCountView.as_view()),
    path('register/', RegisterView.as_view()),
    path('sms_codes/<mobile>/', MsmCodeView.as_view()),
]
