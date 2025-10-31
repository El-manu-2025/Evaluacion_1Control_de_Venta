"""
WSGI config for Control_de_Venta project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Ensure the project root is on sys.path so the inner package `Control_de_Venta`
# can be imported regardless of the process current working directory. In
# deployment environments (Railway/Render) Gunicorn may import this module
# directly and the CWD may not include the repo root.
current_dir = os.path.dirname(__file__)  # .../Control_de_Venta/Control_de_Venta
project_root = os.path.dirname(current_dir)  # .../Control_de_Venta
if project_root not in sys.path:
	sys.path.insert(0, project_root)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Control_de_Venta.settings')


application = get_wsgi_application()
