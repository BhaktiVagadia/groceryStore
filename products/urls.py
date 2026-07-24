from django.urls import path
from . import views


urlpatterns = [
    path('', views.list, name='products'),
    path('sku/<str:sku>/', views.productDetail, name='product_detail'),
    path('notifyMe/<int:product_id>',views.notifyMe,name='notify_me'),

]
