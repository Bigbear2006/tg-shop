from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Client(models.Model):
    id = models.PositiveBigIntegerField(
        verbose_name='Телеграм ID',
        primary_key=True,
    )
    first_name = models.CharField(verbose_name='Имя', max_length=255)
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=255,
        null=True,
        blank=True,
    )
    username = models.CharField(verbose_name='Ник', max_length=32)
    is_premium = models.BooleanField(
        verbose_name='Есть премиум',
        default=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    objects: models.Manager

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        return f'@{self.username}'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'is_premium': self.is_premium,
        }


class Category(models.Model):
    title = models.CharField(verbose_name='Название', max_length=255)
    parent_category = models.ForeignKey(
        'self',
        models.SET_NULL,
        'subcategories',
        null=True,
        blank=True,
        verbose_name='Главная категория',
    )
    objects: models.Manager

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['title']

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(verbose_name='Название', max_length=255)
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=9,
        decimal_places=2,
    )
    image = models.ImageField(verbose_name='Фото', upload_to='products')
    image_tg_id = models.TextField(
        verbose_name='ID фото в телеграм',
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        models.CASCADE,
        'products',
        verbose_name='Категория',
    )
    objects: models.Manager

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['title']

    def __str__(self):
        return self.title


class Dispatch(models.Model):
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True)
    objects: models.Manager

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
