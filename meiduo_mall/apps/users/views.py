from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.users.models import User

"""
判用戶名是否存在
  前端：
  
  后端：
  

"""

class UsernameCountView(View):
    def get(self, request, username):
        print(username)
        count = User.objects.filter(username=username).count()
        return JsonResponse({"count": count, "code": "0", "errmsg": "ok"})


