import json
import re

from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

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


class MobileCountView(View):
    def get(self, request, mobile):
        print(mobile)
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({"count": count, "code": "0", "errmsg": "ok"})


"""
前端：用户输入手机号， 点击获取短信验证码， 发送 axiou 请求 

后端：
    接收请求； 参数 1，手机号，2图片验证码，3.uuid， 
    逻辑：    验证参数 图片验证码，生成短信验证码， 存入redis 数据库，  发送短信
    响应  路由 "sms_codes/<mobile>/?image_code=xxx&image_code_id =xxxxx"
"""


class MsmCodeView(View):
    def get(self, request, mobile):
        # 1. 获取参数，
        mobile = mobile
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        #  2.  验证参数， 是否存在
        if not all([image_code, uuid]):
            return JsonResponse({'code': 400, 'errmsg': "参数不全"})
        # 3. 图片验证码
        redis_cli = get_redis_connection("image_code")
        redis_image_code = redis_cli.get(uuid)
        # 删除图片验证码
        try:
            redis_cli.delete(uuid)
        except Exception as e:
            print("删除图片验证码")

        # 3.2判断是否过有效期
        if redis_image_code is None:
            return JsonResponse({'code': 400, 'errmsg': "图片验证码过期"})

        # 3.3用户发过来的对比 redis_image_code是二进制 需要decode
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': 400, 'errmsg': "图片验证码输入错误"})

        # 4. 生成短信验证码
        # 0-999999
        from random import randint
        # "%06d" 让数字保存6位  如果不够 左侧补0
        sms_code = "%06d" % randint(0, 999999)
        print("sms_code", sms_code)

        # 防止发送短信 频繁
        send_flag = redis_cli.get("send_flag_%s" % mobile)
        if send_flag:
            return JsonResponse({'code': 400, 'errmsg': "短信发送过于频繁 "})

        # 创建Redis 管道
        pl = redis_cli.pipeline()
        pl.setex("send_flag_%s" % mobile, 60, 1)
        pl.setex("sms_%s" % mobile, 300, sms_code)

        # 5. 保存短信验证码到redis
        # redis_cli.setex()
        # 执行请求
        pl.execute()
        # 6. 发送短信
        from utils.sms.SendMessage import Sms
        Sms().send_message(mobile, (sms_code, 5))
        # 7 返回响应
        return JsonResponse({'code': 0, 'errmsg': "ok"})


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
        if not all([username, password, password2, mobile, sms_code, allow]):
            return JsonResponse({"code": "400", "errmsg": "register fail"})

        # 3.2正则验证
        # 用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({"code": "400", "errmsg": "username register fail"})

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return JsonResponse({"code": "400", "errmsg": "mobile register fail"})

        try:
            # uesr = User(username=username, password=password, mobile=mobile)
            # user.save();
            # User.objects.create(username=username, password=password, mobile=mobile)
            # 密码加密 ----
            user = User.objects.create_user(username=username, password=password, mobile=mobile)

            # 状态保持  session
            login(request, user)

        except Exception as e:
            print(e)
            print('数据库失败------->>>')
            return JsonResponse({"code": "400", "errmsg": "register fail"})

        return JsonResponse({"code": "0", "errmsg": "ok"})
