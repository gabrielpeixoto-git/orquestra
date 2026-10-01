import os

from dotenv import load_dotenv

load_dotenv()

env = os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.local")

if env == "config.settings.local":
    from .settings.local import *  # noqa: F401, F403
elif env == "config.settings.test":
    from .settings.test import *  # noqa: F401, F403
elif env == "config.settings.production":
    from .settings.production import *  # noqa: F401, F403
else:
    from .settings.base import *  # noqa: F401, F403
