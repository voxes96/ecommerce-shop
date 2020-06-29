from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    # transaction_number = models.IntegerField()
    order_date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return 'Transaction_%s' % self.pk


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT)

    def __str__(self):
        return '%s %s' % (self.transaction, self.product)
