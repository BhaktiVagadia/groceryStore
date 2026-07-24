from django.urls import path
from . import views

urlpatterns = [
    path('track-order/', views.track_order, name='track_order'),
    path('order/<int:order_id>/cancel-order/', views.cancel_order, name='cancel_order')

]