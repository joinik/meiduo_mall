import json

from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.contents.models import ContentCategory
from apps.contents.utils import get_categories
from apps.goods.models import GoodsCategory, SKU

# 需求 根据点击的分类获取 分类数据
# 前端　　　前端　用户点击　三级分类　　显示列表页　会发送一个ａｘｉｏｓ请求　
# '/list/分类id/skus/'  同时传递过来　了　分页和排序的数据

# 后端　
# 请求　　　参数　　categoryid  page  pagesize  ordering
# 业务逻辑   查询 三级导航数据  然后是 所有的sku商品数据

# 转为字典  返回 json数据

# get请求   /list/<category_id>/skus/
from apps.goods.utils import get_breadcrumb, get_goods_specs


class ListView(View):
    def get(self, request, category_id):
        """提供商品列表页"""
        # 1. 获取参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        # 判断category_id是否正确
        try:
            # 获取三级菜单分类信息:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            print("<>>>>>>>>")
            print(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '获取mysql数据出错'})

        # 查询面包屑导航(函数在下面写着)
        breadcrumb = get_breadcrumb(category)
        print('面包屑》》》》')
        print(breadcrumb)
        # 排序方式:
        try:
            skus = SKU.objects.filter(category=category,
                                      is_launched=True).order_by(ordering)
        except Exception as e:
            print("<>>>>>>>>")
            print(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '获取mysql数据出错'})

        paginator = Paginator(skus, page_size)
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page)
        except EmptyPage:
            # 如果page_num不正确，默认给用户400
            return JsonResponse({'code': 400,
                                 'errmsg': 'page数据出错'})
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表:
        sku_list = []
        # 整理格式:
        for sku in page_skus:
            sku_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        # 把数据变为 json 发送给前端
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': sku_list,
            'count': total_page
        })


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""

        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 拼接json 数据
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                "id": sku.id,
                "default_image_url": sku.default_image.url,
                "name": sku.name,
                "price": sku.price
            })
        return JsonResponse({"code": 0, "errmsg": "ok", "hot_skus": hot_skus})


# 导入:
from haystack.views import SearchView


class MySearchView(SearchView):
    '''重写SearchView类'''

    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情页"""
        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)
        # 查询SKU规格信息
        goods_specs = get_goods_specs(sku_id)

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }
        return render(request, 'detail.html', context)



"""

前端点击进入详情页面会自动发送一个axios请求带着分类id过来
后端
    接收请求 获取cat_id
    业务逻辑 查询有没有数据没有就添加一条有数据就更新数量
    返回json
    
    post请求'/detail/visit/<cat_id>/';112345678

"""


class DetailVisitView(View):
    """详情页分类商品访问量"""


    def post(self, request, category_id):
        try:
            # 1.获取当前商品
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        # 2.查询日期数据
        from datetime import date
        # 获取当天日期
        today_date = date.today()

        from apps.goods.models import GoodsVisitCount
        try:
            # 3.如果有当天商品分类的数据  就累加数量
            count_data = category.goodsvisitcount_set.get(date=today_date)
        except:
            # 4. 没有, 就新建之后在增加
            count_data = GoodsVisitCount()

        try:
            count_data.count += 1
            count_data.category = category
            count_data.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '新增失败'})

        return JsonResponse({'code': 0, 'errmsg': 'OK'})



"""

1  只有登录用户可以访问
2 有顺序按照时间
3 美多只显示5条没有分页

功能
    添加浏览记录用户访问到商品详情页的时候
    查询返回浏览记录用户进入用户中心
    
数据保存
mysql（频繁访问效率不高）商品id  用户id  顺序（时间）
redis 内存足够大
使用redis的List类型保存

前端  点击进入详情页面 会自动发送一个axios请求  带着sku_id过来
后端
	接收请求  获取sku_id
	业务逻辑 连接redis 去重复  保存到redis  保存5条
	返回json
		
post请求  /browse_histories/
参数 sku_id: xxx

redis格式

key                            value
history_userId                  [sku_id,sku_id,sku_id,sku_id,sku_id]

"""



from apps.goods.models import SKU
from django_redis import get_redis_connection
from utils.viewsMixin import LoginRequiredJSONMixin


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """用户浏览记录"""

    def post(self, request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': 'sku不存在'})

        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id

        # 先去重
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再存储
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()

        # 响应结果
        return JsonResponse({'code': 0, 'errmsg': 'OK'})

    def get(self, request):
        # - 获取用户id
        # 取出登录的user对象
        user = request.user
        # - 连接redis
        redis_conn = get_redis_connection('history')
        # - redis获取历史浏览记录的商品id
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, -1)

        # - 根据商品id获取商品sku对象 转为字典
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        # - 返回json数据
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'skus': skus})