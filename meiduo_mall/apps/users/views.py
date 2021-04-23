import json
import re

from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.users.models import User
from apps.users.utils import generate_verify_email_url, check_verify_email_url
from celery_tasks.email.tasks import logger

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



"""
判断手机号是否重复注册
前端：用户输入手机号，失去焦点， 发送一个axios(ajax)请求
后端：
    接收请求，： 接收用户
	路由； get mobiles/<phone:mobile>/count/
	业务逻辑：
		根据手机号，查询数据库， 查询当前数量， 数量大于0说明已经注册过了
	响应：json格式
		{"count":1, "code": "0", "errmsg": "ok"}
"""
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
    def post(self, request):

        # 1 获取参数
        data_dict = json.loads(request.body)
        username = data_dict.get("username")
        password = data_dict.get("password")
        remembered = data_dict.get("remembered")

        # 2 校验 参数
        if not all([username, password]):
            return JsonResponse({"code": "400", "errmsg": "参数不全"})

        # 根据用户输入的username 判断是手机号还是用户名
        # 然后 设置用户验证是使用用户名还是 手机号
        if re.match(r"1[3-9]\d{9}$", username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        # 3 验证用户
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({"code": "400", "errmsg": "用户名或者密码错误"})

        # 4 session 保存
        login(request, user)

        # 5 保持登录状态  判断是否记住登录 设置session的有效期
        if not remembered:
            request.session.set_expiry(0)

        else:
            # 默认为 2周
            request.session.set_expiry(None)

        # 6 返回响应
        http = JsonResponse({"code": "0", "errmsg": "登录成功"})
        http.set_cookie("username", user.username, max_age=3600 * 24 * 5)
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


from utils.viewsMixin import LoginRequiredJSONMixin


class UserInfoView(LoginRequiredJSONMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""

        # 获取界面需要的数据,进行拼接
        info_data = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }

        # 返回响应
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'info_data': info_data})


"""
添加邮箱

前端： 用户输入邮箱，用户点击保存，发送请求

后端：
    接收请求   
    业务逻辑:
        验证邮箱 参数， 
    路由 put '/emails/' 
    响应：json数据
        {'code': 0, 'errmsg': '添加邮箱成功'}
        {'code': 400, 'errmsg': '邮箱错误'}
        
"""
from django import http


class SaveEmailView(View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '参数email有误'})

        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '添加邮箱失败'})

        # 异步发送验证邮件
        from celery_tasks.email.tasks import send_verify_email
        # 生成验证链接
        # verify_url = '邮件验证链接'
        verify_url = generate_verify_email_url(request.user)
        subject = "美多商城邮箱验证"
        # 拼接 邮件内容
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

        send_verify_email.delay(subject=subject, to_email=email, html_message=html_message)

        # 响应添加邮箱结果
        return http.JsonResponse({'code': 0, 'errmsg': '添加邮箱成功'})


"""验证邮箱"""


class VerifyEmailView(View):
    def put(self, request):
        print('-----验证邮箱-----')
        # 1, 获取token
        token = request.GET.get('token')
        # 2. 解密token
        user = check_verify_email_url(token)
        # 3. 数据库验证，
        try:
            user = User.objects.filter(id=user.id, email=user.email).get()
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '参数有误'})

        # 4. 设置邮箱已激活
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            print(e)
        return JsonResponse({'code': 0, 'errmsg': '邮箱激活成功'})




"""修改密码"""
class UpdataPassword(LoginRequiredJSONMixin,View):
    def put(self,request):
        # 接收参数
        body_dict = json.loads(request.body)
        old_password = body_dict.get('old_password')
        new_password = body_dict.get('new_password')
        new_password2 = body_dict.get('new_password2')
        # 进行参数 校验
        if not all([old_password,new_password,new_password2]):
            return JsonResponse({'code': 400, 'errmsg': '参数有误'})

        if old_password == new_password or new_password2 != new_password or old_password == new_password2:
            return JsonResponse({'code': 400, 'errmsg': '参数有误'})

        # 与原始密码对比
        result = request.user.check_password(old_password)
        if not result:
            return JsonResponse({'code': 400,
                                      'errmsg': '原始密码不正确'})
        try:

        # 进行数据库查询
            user = User.objects.get(id=request.user.id)
            user.set_password(new_password2)
            user.save()
        # 进行数据修改
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': 'fail'})

        # 清除session
        logout(request, user)

        http = JsonResponse({'code': 0, 'errmsg': '密码修改成功'})
        http.delete_cookie("username")

        # 返回响应
        return http

