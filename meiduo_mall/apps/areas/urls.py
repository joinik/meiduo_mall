from django.urls import path, re_path

from apps.areas.views import AreasView, SubsView, CreateAddressView, ShowAddressView, DeleteAddressView, \
    DefaultAddressView, UpdateTitleView

#

urlpatterns = [
    path('areas/', AreasView.as_view()),
    re_path(r'^areas/(?P<pk>[1-9]\d+)/$', SubsView.as_view()),
    path('addresses/create/', CreateAddressView.as_view()),
    path('addresses/', ShowAddressView.as_view()),
    path('addresses/<add_id>/default/', DefaultAddressView.as_view()),
    path('addresses/<add_id>/', DeleteAddressView.as_view()),
    path('addresses/<add_id>/title/', UpdateTitleView.as_view()),

]
