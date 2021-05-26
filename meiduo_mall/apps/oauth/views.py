import json

from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from QQLoginTool.QQtool import OAuthQQ

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generate_access_token, check_access_token
from apps.users.models import User
from django.conf import settings
from utils.weiboOauthTool import OAuthWeibo

"""
生成跳转的链接
前端  用户点击qq登录按钮，发送一个 axios请求  /qq/authorization/

后端
	接收请求
	逻辑  使用QQloginTool生成跳转链接
	响应  返回链接  {"code":0,"login_url":'http://xxx.qq.com/fdfds'}
	路由  get  /qq/authorization/
"""


class QQLoginUrlView(View):
    def get(self, request):
        # - 1使用QQloginTool生成跳转链接

        # 1.1 生成 oauth对象
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state='abc')
        # 获取扫码后的 authorization code
        login_url = oauth.get_qq_url()
        # - 2返回响应
        return JsonResponse({'code': 0, "login_url": login_url})


"""
需求  获取code  根据code获取token  根据  token获取openid

前端：
    发送axios请求 把code发送给后端  /oauth_callback/?code=fjdsskfklsdjl

后端
	接收请求 接收参数 code
	逻辑   根据code获取token  根据  token获取openid

	响应
	路由  get /oauth_callback/?code=fjdsskfklsdjl
"""


class OauthView(View):
    def get(self, request):
        # 1获取code
        code = request.GET.get("code")
        print('获取code:', code)
        # 2根据code获取token
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state='abc')
        token = oauth.get_access_token(code)
        print('获取token', token)
        # 3根据token获取openid
        openid = oauth.get_open_id(token)
        print('openid', openid)
        # 4根据openid 去数据库查询 QAuthQQuser 账号信息
        try:
            qquesr = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            # 不存在捕获异常  并且返回 加密的openid
            print(e)
            # 加密的openid
            openid = generate_access_token(openid)
            print('openid ----加密', openid)
            return JsonResponse({'code': 400, 'access_token': openid})
        else:
            # 如果存在，返回正常的数据， 保持登录状态
            login(request, qquesr.user)
            # cookie
            resp = JsonResponse({'code': 0, 'errmsg': 'ok'})
            resp.set_cookie('username', qquesr.user.username)

            return resp
    def post(self,request):
        # 接收请求
        body_dict = json.loads(request.body)
        # 2 获取请求参数，手机号，密码，短信验证码
        password = body_dict.get('password')
        mobile = body_dict.get('mobile')
        sms_code = body_dict.get('sms_code')
        openid = body_dict.get('access_token')

        # 对openid 解密 获取源数据
        openid = check_access_token(openid)
        print('解密----openid',openid)

        # 验证参数省略
        # 根据手机号， 查询是否已经注册
        try:
            user = User.objects.get(mobile = mobile)
        except Exception as e:
            print(e)
            # 捕获异常，说明没有注册，创建 user对象，绑定 用户和openid
            user = User.objects.create_user(username=mobile,mobile=mobile,password=password)
        else:
            # 用户存在， 进行进行 密码验证
            if not user.check_password(password):
                return JsonResponse({'code':400,'errmsg':'账号或密码错误'})

        try:
            # 绑定user， openid
            OAuthQQUser.objects.create(user=user,openid=openid)
        except Exception as e:
            print(e)
            return JsonResponse({'code':400,'errmsg':'账号已绑定，无法绑定'})
        # 6 状态保持
        login(request, user)
        response = JsonResponse({"code": 0, "errmsg": "ok"})
        response.set_cookie("username", user.username)

        # 7 返回响应
        return response


class WEIBOLoginUrlView(View):
    def get(self, request):
        # - 1使用QQloginTool生成跳转链接

        # 1.1 生成 oauth对象
        oauth = OAuthWeibo(
            client_id=settings.WEIBO_Key,
            client_secret=settings.WEIBO_Secret,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state='abc')
        # 获取扫码后的 authorization code
        login_url = oauth.get_weibo_url()
        # - 2返回响应
        return JsonResponse({'code': 0, "login_url": login_url})

class WeiboOauthView(View):
    def get(self, request):
        # 1获取code
        code = request.GET.get("code")
        print('获取code:', code)
        # 2根据code获取token
        oauth = OAuthWeibo(
            client_id=settings.WEIBO_Key,
            client_secret=settings.WEIBO_Secret,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state='abc')
        token = oauth.get_access_token(code)
        print('获取token', token)
        # 3根据token获取openid
        openid = oauth.get_uid(token)
        print('openid', openid)
        # 4根据openid 去数据库查询 QAuthQQuser 账号信息
        try:
            qquesr = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            # 不存在捕获异常  并且返回 加密的openid
            print(e)
            # 加密的openid
            openid = generate_access_token(openid)
            print('openid ----加密', openid)
            return JsonResponse({'code': 400, 'access_token': openid})
        else:
            # 如果存在，返回正常的数据， 保持登录状态
            login(request, qquesr.user)
            # cookie
            resp = JsonResponse({'code': 0, 'errmsg': 'ok'})
            resp.set_cookie('username', qquesr.user.username)

            return resp
    def post(self,request):
        # 接收请求
        body_dict = json.loads(request.body)
        # 2 获取请求参数，手机号，密码，短信验证码
        password = body_dict.get('password')
        mobile = body_dict.get('mobile')
        sms_code = body_dict.get('sms_code')
        openid = body_dict.get('access_token')

        # 对openid 解密 获取源数据
        openid = check_access_token(openid)
        print('解密----openid',openid)

        # 验证参数省略
        # 根据手机号， 查询是否已经注册
        # try:
        #     user = User.objects.get(mobile = mobile)
        # except Exception as e:
        #     print(e)
        #     # 捕获异常，说明没有注册，创建 user对象，绑定 用户和openid
        #     user = User.objects.create_user(username=mobile,mobile=mobile,password=password)
        # else:
        #     # 用户存在， 进行进行 密码验证
        #     if not user.check_password(password):
        #         return JsonResponse({'code':400,'errmsg':'账号或密码错误'})
        #
        # try:
        #     # 绑定user， openid
        #     OAuthQQUser.objects.create(user=user,openid=openid)
        # except Exception as e:
        #     print(e)
        #     return JsonResponse({'code':400,'errmsg':'账号已绑定，无法绑定'})
        # # 6 状态保持
        # login(request, user)
        # response = JsonResponse({"code": 0, "errmsg": "ok"})
        # response.set_cookie("username", user.username)
        #
        # # 7 返回响应
        # return response
        return JsonResponse({"code": 0, "errmsg": "ok"})