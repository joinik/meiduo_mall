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
from apps.goods.utils import get_breadcrumb


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
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_dy('-sales')[:2]

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
        # goods_specs = goods_specs = get_goods_and_spec(sku_id)

        # 渲染页面
        context = {
            'categories':categories,
            'breadcrumb':breadcrumb,
            'sku':sku,
        }
        return render(request, 'detail.html', context)