from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings

from apps.users.models import User


def generate_verify_email_url(user):
    """
    生成邮箱验证链接
    :param user: 当前登录用户
    :return: verify_url
    """
    # serializer = Serializer(密钥, expires_in=3600)

    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    data = {'user_id': user.id, 'email': user.email}
    token = serializer.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    print('验证url 生成-------》》》')
    print(verify_url)
    return verify_url


def check_verify_email_url(token):
    """
    生成邮箱验证链接
    :param user: 当前登录用户
    :return: verify_url
    """
    # serializer = Serializer(密钥, expires_in=3600)

    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    # 解密
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    else:
        user_id = data.get('user_id')
        email = data.get('email')
        print('解密email',email)
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            return None
        else:
            return user

