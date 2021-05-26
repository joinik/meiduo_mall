from django.urls import path, re_path

from apps.goods import views
from apps.goods.views import ListView, HotGoodsView, DetailView

urlpatterns = [
    path('list/<category_id>/skus/', ListView.as_view()),
    path('hot/<category_id>/', HotGoodsView.as_view()),
    path('search/', views.MySearchView()),
    re_path(r'detail/(?P<sku_id>\d+)/', DetailView.as_view()),

]