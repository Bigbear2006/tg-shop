from aiogram import types
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ClientManager(models.Manager):
    async def from_tg_user(self, user: types.User) -> 'Client':
        return await self.acreate(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            is_premium=user.is_premium or False,
        )

    async def update_from_tg_user(self, user: types.User) -> None:
        await self.filter(pk=user.id).aupdate(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            is_premium=user.is_premium or False,
        )

    async def create_or_update_from_tg_user(
            self,
            user: types.User,
    ) -> tuple['Client', bool]:
        try:
            client = await self.aget(id=user.id)
            await self.update_from_tg_user(user)
            await client.arefresh_from_db()
            return client, False
        except ObjectDoesNotExist:
            return await self.from_tg_user(user), True


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
    objects = ClientManager()

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
            'last_name': self.last_name or '',
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
        return f'{self.title} ({int(self.price):,} ₽)'


class Dispatch(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Вы можете использовать переменные: '
                  '${id}, ${username}, ${first_name}, ${last_name}',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    objects: models.Manager

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
