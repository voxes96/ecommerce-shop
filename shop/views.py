from django.shortcuts import render
from .models import Product


def index(request):
    products_list = Product.objects.filter(active=True)
    return render(request, 'shop/index.html', {'products_list': products_list})
