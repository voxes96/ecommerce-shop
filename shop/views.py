from django.shortcuts import render, get_object_or_404
from .models import Product


def index(request):
    products_list = Product.objects.filter(active=True)
    return render(request, 'shop/index.html', {'products_list': products_list})


def detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'shop/detail.html', {'product': product})
