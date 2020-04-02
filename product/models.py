from django.db import models
from shared.models import TimeStampedModel


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'


class Product(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)
    price = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='product')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
