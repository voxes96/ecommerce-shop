from django.urls import path

from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.index, name='index'),
    path('detail/<int:product_id>', views.detail, name='detail'),
    path('basket', views.basket, name='basket'),
    path('basket/add/<int:product_id>', views.add_to_basket, name='add-to-basket'),
    path('basket/update/<int:product_id>', views.update_basket, name='update-basket'),
    path('basket/buy', views.buy_basket, name='buy-basket'),
    path('basket/clear', views.clear_basket, name='clear-basket')
]
