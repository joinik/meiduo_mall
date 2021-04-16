from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from utils.captcha.captcha import captcha

"""
图片验证码
前端： 用户点击 图片验证码 生成 UUID，拼接url ， 发送 请求
后端：
    请求 get   地址里的UUID
    路由  get '/inage_codes/<uuid>/'
    业务逻辑： 接收uuid ，生成 图片验证码 ，保存到redis 数据库
    响应  返回二进制数据
    
    
"""

class ImageCodeView(View):
    def get(self, request, uuid):

        #  1. 获取uuid，
        print(uuid)
        #   2. 生成验证码图片，二进制数据
        text, image = captcha.generate_captcha()
        print(text)
        #   3. 存到redis UUID作为key
        #   get_redis_connection  获取redis 数据库
        redis_cli = get_redis_connection("image_code")
        #  uuid 为key 120s是过期时间
        redis_cli.setex(uuid,120,text)

        #   4. 返回二进制图片数据
        return HttpResponse(image,content_type='image/jpeg')