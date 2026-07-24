from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

class StaticProductImageStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', None) or []
        base = staticfiles_dirs[0] if staticfiles_dirs else os.path.join(str(settings.BASE_DIR), 'static')
        location = os.path.join(str(base), 'product_images')
        base_url = f"{settings.STATIC_URL.rstrip('/')}/product_images/"
        super().__init__(location=location, base_url=base_url, *args, **kwargs)