import random

import redis
from django.conf import settings
from django.core import mail

from celery_app import app

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)


@app.task
def send_email_with_confirm(email):
    code = str(random.randint(100000, 999999))

    data = f"""
    Рады приветствовать на нашем сайте!
    Проверочный код для подтверждения регистрации (действителен в течении 24 часов):
    <b>{code}</b>
    """

    mail.send_mail(
        "Письмо с подтверждением регистрации",
        data,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

    r.set(email, code, ex=60 * 60 * 24)
