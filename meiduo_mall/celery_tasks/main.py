# celery启动文件
import os
from celery import Celery

# 为celery使用django配置文件进行设置

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")

# 创建celery实例
app = Celery('meiduo_mall')

# 设置
app.config_from_object("celery_tasks.config")


# 自动检测任务
app.autodiscover_tasks(["celery_tasks.sms",'celery_tasks.email'])

