"""
WSGI config for Control_de_Venta project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import importlib

# Add both the project root and its parent to sys.path so different import
# layouts are supported (e.g. when Gunicorn changes the working directory).
current_dir = os.path.dirname(__file__)  # .../Control_de_Venta/Control_de_Venta
project_root = os.path.dirname(current_dir)  # .../Control_de_Venta
project_parent = os.path.dirname(project_root)  # .../ (repo root parent)

for p in (project_root, project_parent):
	if p and p not in sys.path:
		sys.path.insert(0, p)

# Diagnostic output for deployment logs to help troubleshoot import issues.
print('WSGI: current_dir=', current_dir)
print('WSGI: project_root=', project_root)
print('WSGI: project_parent=', project_parent)
print('WSGI: sys.path (head)=', sys.path[:5])

# Try to detect which settings module is importable and set DJANGO_SETTINGS_MODULE
# accordingly (supports both 'Control_de_Venta.settings' and
# 'Control_de_Venta.Control_de_Venta.settings').
SETTINGS_CANDIDATES = [
	'Control_de_Venta.settings',
	'Control_de_Venta.Control_de_Venta.settings',
]
chosen = None
for candidate in SETTINGS_CANDIDATES:
	try:
		# Try importing the full settings module directly. This ensures the
		# specific submodule exists (not just the parent package).
		mod = importlib.import_module(candidate)
		chosen = candidate
		print('WSGI: successfully imported settings module candidate:', candidate)
		# Diagnostic: also import the parent package and list its content.
		pkg_name = candidate.rsplit('.', 1)[0]
		try:
			pkg = importlib.import_module(pkg_name)
			print('WSGI: package', pkg, 'file=', getattr(pkg, '__file__', None))
			print('WSGI: package __path__=', getattr(pkg, '__path__', None))
			if getattr(pkg, '__path__', None):
				p0 = list(pkg.__path__)[0]
				try:
					print('WSGI: package listing for', p0, '=', os.listdir(p0))
				except Exception as e:
					print('WSGI: failed to list package path', p0, '->', e)
		except Exception as e:
			print('WSGI: failed to import parent package for diagnostics:', e)
		break
	except Exception as exc:
		print('WSGI: could not import candidate', candidate, '->', exc)
		continue

if chosen is None:
	# fallback to the first candidate; let Django raise the proper error later
	chosen = SETTINGS_CANDIDATES[0]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', chosen)

# Try importing the full settings module and print any exception to logs so we
# can see the real cause (syntax error, missing dependency, etc.). This does
# not stop execution; Django will re-raise if import fails later, but the
# explicit traceback here helps debugging in deployment logs.
try:
	importlib.import_module(chosen)
	print('WSGI: successfully imported settings module:', chosen)
except Exception as exc:
	import traceback
	print('WSGI: failed to import settings module:', chosen)
	traceback.print_exc()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
