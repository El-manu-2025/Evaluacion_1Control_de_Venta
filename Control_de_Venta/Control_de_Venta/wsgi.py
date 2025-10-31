"""
WSGI config for Control_de_Venta project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Ensure the project root is on sys.path so the inner package can be imported
# regardless of the current working directory used by the process.
current_dir = os.path.dirname(__file__)  # .../Control_de_Venta/Control_de_Venta
project_root = os.path.dirname(current_dir)  # .../Control_de_Venta
project_parent = os.path.dirname(project_root)

for p in (project_root, project_parent):
	if p and p not in sys.path:
		sys.path.insert(0, p)

# Use the explicit settings module that matches how we expose the inner
# package on sys.path in both local and deployed environments. We use the
# single-dotted path because the outer folder (`Control_de_Venta/`) is
# added to sys.path above and the inner package is importable as
# `Control_de_Venta`.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Control_de_Venta.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
