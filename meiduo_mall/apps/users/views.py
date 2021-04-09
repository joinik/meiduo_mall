import json
import re

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.users.models import User

"""
判断用户名是否重复
前端： 用户输入用户名， 失去焦点， 发送一个axios(ajax)请求
后端：
	接收请求，： 接收用户
	路由； get /usernames/<username>/count/
	业务逻辑：
		根据用户名，查询数据库， 查询当前数量， 数量大于0说明已经注册过了
	响应：json格式
		{"count":1, "code": "0", "errmsg": "ok"}
  
"""


class UsernameCountView(View):
    def get(self, request, username):
        print(username)
        count = User.objects.filter(username=username).count()
        return JsonResponse({"count": count, "code": "0", "errmsg": "ok"})


"""
注册
前端: 用户输入 用户名，密码，确认密码 ，手机号，同意协议， 点击注册按钮 发送axios 请求
后端：
    接受请求： 接收json 数据
    路由  post '/register/'
    业务逻辑：验证数据，保存到数据库
    响应 json 格式
        {"code": "0", "errmsg": "ok"}
        {"code": "400", "errmsg": "register fail"}
        
    
"""


class RegisterView(View):
    def post(self, request):
        # 1. 接收数据  json
        # 转换字典
        body_dict = json.loads(request.body)

        # 2. 提取数据
        username = body_dict.get("username")
        password = body_dict.get("password")
        password2 = body_dict.get("password2")
        mobile = body_dict.get("mobile")
        sms_code = body_dict.get("sms_code")
        allow = body_dict.get("allow")

        print(username, password, password2, mobile, sms_code, allow)
        if not (username, password, password2, mobile, sms_code, allow):
            return JsonResponse({"code": "400", "errmsg": "register fail"})

        # 3.2正则验证
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({"code": "400", "errmsg": "register fail"})
        try:
            # uesr = User(username=username, password=password, mobile=mobile)
            # user.save();
            # User.objects.create(username=username, password=password, mobile=mobile)
            # 密码加密 ----
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
            user.save()
        except Exception as e:
            print(e)
            print('数据库失败------->>>')
            return JsonResponse({"code": "400", "errmsg": "register fail"})

        return JsonResponse({"code": "0", "errmsg": "ok"})
