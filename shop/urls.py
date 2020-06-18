from django.urls import path

from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.index, name='index'),
    path('detail/<int:product_id>', views.detail, name='detail'),
]
