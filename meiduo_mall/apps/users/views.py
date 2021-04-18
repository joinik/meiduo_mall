import json
import re

from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse

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
        # print(username)
        count = User.objects.filter(username=username).count()
        return JsonResponse({"count": count, "code": "0", "errmsg": "ok"})


class MobileCountView(View):
    def get(self, request, mobile):
        # print(mobile)
        count = User.objects.filter(mobile=mobile).count()
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
        print('提取数据')
        print(username, password, password2, mobile, sms_code, allow)
        if not all([username, password, password2, mobile, sms_code, allow]):
            return JsonResponse({"code": "400", "errmsg": "register fail"})

        # 3.2正则验证
        # 用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({"code": "400", "errmsg": "username register fail"})

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return JsonResponse({"code": "400", "errmsg": "mobile register fail"})

        # 3. 短信验证码
        redis_cli = get_redis_connection("image_code")
        redis_sms_code = redis_cli.get("sms_%s" % mobile)

        # 3.2判断是否过有效期
        if redis_sms_code is None:
            return JsonResponse({'code': 400, 'errmsg': "短信验证码过期"})

        # 3.3用户发过来的对比 redis_image_code是二进制 需要decode
        if redis_sms_code.decode().lower() != sms_code.lower():
            return JsonResponse({'code': 400, 'errmsg': "短信验证码输入错误"})


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

        http = JsonResponse({"code": "0", "errmsg": "注册成功"})
        # 把用户名保存到cookie 方便在首页显示 有效期产品决定
        http.set_cookie("username", user.username, max_age=3600 * 24 * 5)
        return http





"""
登陆

前端： 用户输入用户名/手机号， 密码 ， 是否记住denglu

后端：
    接受 请求 ：  Post  接收 json数据 验证 用户名， 密码
    逻辑：
        从 数据库取出 用户名 密码  进行验证
        记住登录状态，
    路由： post '/login/'
    响应： 
        json格式
        {"code":"0","errmsg":"ok"}
        {"code":"400","errmsg":"fail"}

"""
class LoginView(View):
    def post(self,request):

        # 1 获取参数
        data_dict = json.loads(request.body)
        username = data_dict.get("username")
        password = data_dict.get("password")
        remembered = data_dict.get("remembered")

        # 2 校验 参数
        if not all([username,password]):
            return JsonResponse({"code": "400", "errmsg": "参数不全"})

        # 根据用户输入的username 判断是手机号还是用户名
        # 然后 设置用户验证是使用用户名还是 手机号
        if re.match(r"1[3-9]\d{9}$", username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'



        # 3 验证用户
        user = authenticate(username=username,password=password)
        if not user:
            return JsonResponse({"code": "400", "errmsg": "用户名或者密码错误"})

        # 4 session 保存
        login(request,user)

        # 5 保持登录状态  判断是否记住登录 设置session的有效期
        if not remembered:
            request.session.set_expiry(0)

        else:
            # 默认为 2周
            request.session.set_expiry(None)

        # 6 返回响应
        http = JsonResponse({"code": "0", "errmsg": "登录成功"})
        http.set_cookie("username",user.username, max_age=3600*24*5)
        return http


"""
退出
前端  ：用户 在首页点击退出 发送一个axios请求
后端 :
  
    路由:post 'http://www.meiduo.site:8000/logout/'

    业务逻辑： 清空session 和cookie 返回响应
    响应 JSON格式
    {"code": "0", "errmsg": "OK"}
    {"code": "400", "errmsg": "login fail"}

"""


class LogoutView(View):
    def delete(self, request):
        # 1调用logout清空状态保持的session

        logout(request)

        # 2删除cookie里的username
        response = JsonResponse({"code": "0", "errmsg": "ok"})
        response.delete_cookie('username')

        # 3返回响应

        return response