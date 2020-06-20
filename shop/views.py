from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import Product
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
    return render(request, 'shop/basket.html')


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

