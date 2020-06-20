from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .models import Product, Order
import logging

logger = logging.getLogger(__name__)


def index(request):
    # del request.session['basket']
    # del request.session['basket_size']
    products_list = Product.objects.filter(active=True)
    return render(request, 'shop/index.html', {'products_list': products_list})


def detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'shop/detail.html', {'product': product})


def basket(request):
    products = []
    total_price = 0
    for bs in request.session['basket']:
        p = get_object_or_404(Product, pk=int(bs['item']))
        p.basket = int(bs['amount'])
        p.price_sum = p.basket * p.price
        total_price += p.price_sum
        products.append(p)
    return render(request, 'shop/basket.html', {'products': products, 'total_price': total_price})


def add_to_basket(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    try:
        if 'basket' not in request.session:
            request.session['basket'] = []
        if 'basket_size' not in request.session:
            request.session['basket_size'] = 0

        in_basket = False
        size = request.POST['basket-quantity']

        for bs in request.session['basket']:
            if int(bs['item']) == product_id:
                if int(size) + int(bs['amount']) > product.quantity:
                    size = product.quantity - int(bs['amount'])
                bs['amount'] = int(size) + int(bs['amount'])
                request.session['basket_size'] = int(size) + int(request.session['basket_size'])
                in_basket = True

        if not in_basket:
            request.session['basket'].append({'item': product_id, 'amount': size})
            request.session['basket_size'] = int(size) + int(request.session['basket_size'])

        request.session.modified = True
    except KeyError:
        return HttpResponseRedirect(reverse('shop:detail', args=(product_id,)))
    else:
        return HttpResponseRedirect('/')


def update_basket(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    size = request.POST['basket-update']
    for bs in request.session['basket']:
        if int(bs['item']) == product_id:
            if int(size) > product.quantity:
                size = product.quantity
            elif int(size) < 0:
                size = 0
            size_diff = int(size) - int(bs['amount'])
            bs['amount'] = int(size)

            if int(size) == 0:
                request.session['basket'].remove(bs)

            request.session['basket_size'] = int(size_diff) + int(request.session['basket_size'])
            request.session.modified = True

    return HttpResponseRedirect(reverse('shop:basket'))


def buy_basket(request):
    for bs in request.session['basket']:
        product = get_object_or_404(Product, pk=int(bs['item']))
        size = int(bs['amount'])
        price = size * product.price

        product.quantity -= size
        product.save()

        o = Order(product=product, order_date=timezone.now(), quantity=size, totalPrice=price)
        o.save()

    if 'basket' in request.session:
        request.session['basket'] = []
    if 'basket_size' in request.session:
        request.session['basket_size'] = 0

    return HttpResponseRedirect(reverse('shop:basket'))


def clear_basket(request):
    if 'basket' in request.session:
        request.session['basket'] = []
    if 'basket_size' in request.session:
        request.session['basket_size'] = 0
    return HttpResponseRedirect(reverse('shop:basket'))
