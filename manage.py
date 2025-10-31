#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
  
    base_dir = os.path.abspath(os.path.dirname(__file__))
    candidate_a = os.path.join(base_dir, 'Control_de_Venta')
    candidate_b = os.path.join(candidate_a, 'Control_de_Venta')
    # Prepend candidate paths if they exist so imports resolve correctly.
    for p in (candidate_a, candidate_b):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)

    # Default settings module (keep compatibility with nested layout)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Control_de_Venta.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
