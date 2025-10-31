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

# Diagnostic check: ensure the package `Control_de_Venta` is importable from
# the modified sys.path. If not, emit a compact diagnostic to stderr so the
# deployment logs show why the import fails (useful for Render/Railway).
try:
	import importlib.util
	spec = importlib.util.find_spec('Control_de_Venta')
	if spec is None:
		# Print minimal diagnostic and continue — Django will raise the
		# ModuleNotFoundError later but logs will include these lines.
		sys.stderr.write('\n[WSGI DIAGNOSTIC] Control_de_Venta package NOT found in sys.path.\n')
		sys.stderr.write(f'[WSGI DIAGNOSTIC] sys.path (first 6 entries): {sys.path[:6]}\n')
		# List directory contents for the likely project_root to help debug
		try:
			import os
			entries = os.listdir(project_root)
			sys.stderr.write(f'[WSGI DIAGNOSTIC] project_root={project_root} contents: {entries}\n')
		except Exception:
			pass
	else:
		sys.stderr.write('[WSGI DIAGNOSTIC] Control_de_Venta package found via importlib.util.find_spec\n')
except Exception:
	# Best-effort diagnostics; don't break startup here.
	pass

# Use the explicit settings module that matches how we expose the inner
# package on sys.path in both local and deployed environments. We use the
# single-dotted path because the outer folder (`Control_de_Venta/`) is
# added to sys.path above and the inner package is importable as
# `Control_de_Venta`.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Control_de_Venta.Control_de_Venta.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
