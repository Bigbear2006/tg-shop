import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Dispatch
from shop.tasks import send_dispatch

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Dispatch)
def after_dispatch_create(sender, instance, created, **kwargs):
    if created:
        logger.info(f'Dispatch id={instance.pk} was created')
        send_dispatch.delay(instance.text)
