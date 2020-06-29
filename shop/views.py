from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
import requests, json
from .utils import PAYMENT_CONFIG

from .models import Product, Order, Transaction
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
    if 'basket' in request.session:
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
    products = []
    price_total = 0
    for bs in request.session['basket']:
        product = get_object_or_404(Product, pk=int(bs['item']))
        size = int(bs['amount'])
        price = size * product.price
        price_total += price
        products.append({
            'name': product.name,
            'unitPrice': str(int(product.price * 100)),
            'quantity': str(int(size))
        })
    price_total = int(price_total * 100)

    header = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 3e5cac39-7e38-4139-8fd6-30adc06a61bd'
    }
    body = {
        "notifyUrl": "https://ecommerceshop.free.beeceptor.com/notify",
        "customerIp": "127.0.0.1",
        "merchantPosId": "145227",
        "description": "Przykladowe zamowienie na potrzeby projektu",
        "currencyCode": "PLN",
        "totalAmount": str(price_total),
        "buyer": {
            "email": "szymon.liszka@example.com",
            "phone": "123123123",
            "firstName": "Szymon",
            "lastName": "Liszka",
            "language": "pl"
        },
        "settings": {
            "invoiceDisabled": "true"
        },
        "products": products
    }
    r = requests.post('https://secure.payu.com/api/v2_1/orders', headers=header, json=body)

    if str(r.status_code).startswith('2'):
        save_transaction(request)
        return render(request, 'shop/buy.html', {'redirect_url': r.url})
    else:
        return render(request, 'shop/error.html')

    # nie dziala z powodu nie dzialajacej strony - prace konserwacyjne
    # r = requests.post('https://secure.snd.payu.com/pl/standard/user/oauth/authorize', params=PAYMENT_CONFIG['OAuth'])
    #
    # if str(r.status_code).startswith('2'):
    #     logger.info(r.request)
    #     logger.info(r.json())
    #     logger.info(r.json()['access_token'])
    #     logger.info(PAYMENT_CONFIG['loging'])
    #
    #     header = {
    #         "Content-Type": PAYMENT_CONFIG['Content-Type'],
    #         "Authorization": PAYMENT_CONFIG['Authorization'] + ' ' + r.json()['access_token']
    #     }
    #     body = {
    #         "notifyUrl": PAYMENT_CONFIG['notifyUrl'],
    #         "customerIp": PAYMENT_CONFIG['customerIp'],
    #         "merchantPosId": PAYMENT_CONFIG['merchantPosId'],
    #         "description": "Zakupy za pomoca przykladowego sklepu PayU",
    #         "currencyCode": PAYMENT_CONFIG['currencyCode'],
    #         "totalAmount": str(price_total),
    #         "settings": PAYMENT_CONFIG['settings'],
    #         "products": products
    #     }
    #
    #     r = requests.post('https://secure.snd.payu.com/api/v2_1/orders', headers=header, json=body)
    #
    #     save_transaction(request)
    #
    #     return render(request, 'shop/buy.html', {'redirect_url': r.url})
    # else:
    #     return render(request, 'shop/error.html')


def clear_basket(request):
    if 'basket' in request.session:
        request.session['basket'] = []
    if 'basket_size' in request.session:
        request.session['basket_size'] = 0
    return HttpResponseRedirect(reverse('shop:basket'))


def save_transaction(req):
    transaction = Transaction(order_date=timezone.now(), price=0)
    transaction.save()

    price_total = 0
    for bs in req.session['basket']:
        product = get_object_or_404(Product, pk=int(bs['item']))
        size = int(bs['amount'])
        price = size * product.price
        price_total += price

        product.quantity -= size
        product.save()

        o = Order(product=product, quantity=size, transaction=transaction)
        o.save()

    transaction.price = price_total
    transaction.save()

    if 'basket' in req.session:
        req.session['basket'] = []
    if 'basket_size' in req.session:
        req.session['basket_size'] = 0
