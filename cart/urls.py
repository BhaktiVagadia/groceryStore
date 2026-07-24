from django.urls import path
from . import views

urlpatterns = [
    path('', views.cartDetail, name='cartDetail'),
    path('checkout/', views.checkout, name='checkout'),
    path('saveAddress/', views.saveAddress, name='saveAddress'),
    path('addToCart/<int:product_id>/', views.addToCart, name='addToCart'),
    path('delete/<int:item_id>/', views.deleteCartItem, name='deleteCartItem'),
    path('empty-cart/', views.empty_cart, name='empty_cart'),
    path('placeOrder/', views.placeOrder, name='place_order'),
    path('applyCartCoupon/', views.apply_cart_coupon, name='apply_cart_coupon'),

]