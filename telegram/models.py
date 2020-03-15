from django.db import models
from shared.models import TimeStampedModel
from product.models import Product


class TgUser(TimeStampedModel):
    user_id = models.IntegerField()
    step = models.IntegerField(default=0)
    first_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'{self.user_id}'


class Cart(TimeStampedModel):
    user = models.ForeignKey(TgUser, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    qty = models.IntegerField(default=0)
    status = models.BooleanField(default=False)


class Order(TimeStampedModel):
    user = models.ForeignKey(TgUser, on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(Cart)

    def __str__(self):
        return f'{str(self.user.user_id) | self.product.name | str(self.qty)}'

