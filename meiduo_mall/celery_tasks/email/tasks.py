import logging
from django.conf import settings
from django.core.mail import send_mail
from celery_tasks.main import app

logger = logging.getLogger('django')

@app.task( name='send_verify_email')
def send_verify_email(subject,to_email,html_message):
    """
    发送验证邮箱邮件
    :param to_email: 收件人邮箱
    :param subject: 邮箱标题
    :param verify_url: 验证链接
    :return: None
    """


    try:
        send_mail(subject, message="", from_email=settings.EMAIL_FROM, recipient_list=[to_email], html_message=html_message)
    except Exception as e:
        logger.error(e)


