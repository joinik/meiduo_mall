# meiduo_mall
美多商城

目录

[1.项目准备](#1. 项目准备 )

[2.用户注册](#2. 用户注册)



### 实现功能

- 用户  登录，注册，功能
- 购物 功能
- 支付 功能

------------------------------

| 日期 | 计划 | 完成情况 |
|  :---  | :---  |  ----  |
| 2021-4-13 | 项目环境 | ✔ |
| 2021-4-16 | 完成用户注册功能 | ✖ |


### 1. 项目准备 

- 环境 

  - ```
    py3
    django 
    ```

  - 

### 2. 用户注册

#### 2.1  用户模型类

- 继承 `AbstractUser`

  ```
  
  class User(AbstractUser):
      mobile = models.CharField(max_length=11,unique=True)
  
      class Meta:
          db_table = 'tb_users'
          verbose_name = '用戶'
          verbose_name_plural = verbose_name
  ```

-  在setting中 添加 `AUTH_USER_MODEL = 'users.User'`

  ![1617867050348](D:%5CPycharm-project%5Cuntitled%5Cmeiduo_mall%5CREADME.assets%5C1617867050348.png)

- **创建视图 判断用户名是否重复注册**

  所有的视图逻辑，	1接收数据   2验证数据  3处理逻辑（包含数据库处理）4 返回响应

  ```
  
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
  
  
  class UsernameView(View):
  	def get(self, request, username):
  		# 1. 接收 数据 打印 用户名
  		print(username)
  		# 2. 根据用户名查数据库
  		conut = User.objects.filter(username=username).count()
  		# 3. 返回响应
  		return JsonResponse({"count": count, "code": "0", "errmsg": "OK"})
  ```

  前端  www.meiduo.site:8080

  后端  www.meiduo.site:8000

#### 2.2  跨域CORS

  **现在，前端与后端分处不同的域名，这就涉及到跨域访问数据的问题，因为浏览器的同源策略，默认是不支持两个不同域间相互访问数据，而我们需要在两个域名间相互传递数据，这时我们就要为后端添加跨域访问的支持。**

  我们使用CORS来解决后端对跨域访问的支持。

  使用django-cors-headers扩展

  [参考文档https://github.com/ottoyiu/django-cors-headers/](https://github.com/ottoyiu/django-cors-headers/)

  - 安装

    ```
    pip install django-cors-headers
    ```

    添加应用

    ```
    INSTALLED_APPS = (
        ...
        'corsheaders',
        ...
    )
    ```

    中间件设置

    ```
    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        ...
    ]
    ```

    白名单 

    ```
    # CORS
    CORS_ALLOWED_ORIGINS = (
        'http://127.0.0.1:8080',
        'http://localhost:8080',
        'http://www.meiduo.site:8080',
        'http://www.meiduo.site:8000'
    )
    CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie
    ```

-   **2.3注册视图  ** 
  
  ```
​```
  注册 
  前端：用户输入，用户名，密码，确认密码，手机号，同意协议，点击注册按钮， 发送axios 请求
  后端：
  	接收请求：post 请求 json 数据
  	路由： post '/register/'
  	业务逻辑： 验证数据， 保存到数据库
  	响应json 格式
  		{"code":0, "errmsg": "ok"}
  		{"code":400, "errmsg": "register fail"}
  		
  	
  		
  ​```
  
  class RegisterView(View):
  	def post(self, request):
  		# 1. 接收数据
  		body_dict = json.loads(request.body)
  		
  		# 2. 提取数据
  		username = body_dict.get("username")
  		password = body_dict.get("password")
  		password2 = body_dict.get("password2")
  		mobile = body_dict.get("mobile")
  		sms_code = body_dict.get("sms_code")
  		allow = body_dict.get("allow")
  		
  		# 3.1. 判断数据是否存在
  		if not (username, password, password2, mobile, sms_code, allow):
  		 	return JsonResponse({"code":400, "errmsg": "register fail"})
  		 	
  		 # 3.2  判断re匹配 username
  		if not re.match(r"^[a-zA-Z0-9_-]{5,20}", username):
  		 	return JsonResponse({"code":400, "errmsg": "register fail"})
  			
  		# 数据保存到数据库
  		# user = User.objects.create(username=username,password=password,mobile=mobile)
  		# user.save()
  		# user = User(username=username,password=password,mobile=mobile)
  		# user.save()
  		try:
              user = User.objects.create_user(username=username,password=password,mobile=mobile)
              user.save()
          except Exception as e:
          	print(e)
          	print('数据库报错》》》》')
  		 	return JsonResponse({"code":400, "errmsg": "register fail"})
          	
          return JsonResponse({"code":0, "errmsg": "ok"})
  		
  		
  
  ```
  
  **postman 发送post**

  ![1617896777639](D:%5CPycharm-project%5Cuntitled%5Cmeiduo_mall%5CREADME.assets%5C1617896777639.png)

  **打印结果**![](D:%5CPycharm-project%5Cuntitled%5Cmeiduo_mall%5CREADME.assets%5C1617896696631.png)

- 图片验证码

  - **通过captcha包 生成图片验证码**

    - ` pip install Pillow  `

  - 测试 视图

    - ```
      from django.http import HttpResponse
      from django.shortcuts import render
      
      # Create your views here.
      from django.views import View
      from django_redis import get_redis_connection
      
      from utils.captcha.captcha import captcha
      
      
      ​```
      图片验证码
      前端：用户点击验证码 生成uuid 拼接url 发送请求
      后端：
      	接收请求  get 
      	路由：get '/image_code/<uuid>/'
      	业务逻辑：获取uuid 生成图片验证码，二进制数据， uuid作为key 存入reids数据库
       	响应 返回二进制数据
       	
      ​```
      
      class IMageCodeView(View):
      	def get(self, request, uuid):
      		# 1.打印图片id
      		print('图片id',uuid)
      		#   2. 生成验证码图片，二进制数据
              text, image = captcha.generate_captcha()
              print('图片验证码数据',text)
              #   3. 存到redis UUID作为key
              #   get_redis_connection  获取redis 数据库
              redis_cli = get_redis_connection("image_code")
              #  uuid 为key 120s是过期时间
              redis_cli.setex(uuid,120,text)
      
              #   4. 返回二进制图片数据
              return HttpResponse(image,content_type='image/jpeg')
      		
      		
      		
      		
      ```

    - 添加 redis    image_code

      ```
      "image_code": { # session
              "BACKEND": "django_redis.cache.RedisCache",
              "LOCATION": "redis://127.0.0.1:6379/2",
              "OPTIONS": {
                  "CLIENT_CLASS": "django_redis.client.DefaultClient",
              }
          },
      ```

    - 添加路由 

      - ```
        urlpatterns = [
        	path('image_codes/<uuid>/', ImageCodeView.as_view()),
        
        ]
        ```

      - 总路由

      - ![1617960390153](D:%5CPycharm-project%5Cuntitled%5Cmeiduo_mall%5CREADME.assets%5C1617960390153.png)

 - 短信验证码注册

   - 1. 使用 容联云 api 服务



