web: bash -lc "/app/.venv/bin/python manage.py migrate && /app/.venv/bin/python manage.py collectstatic --noinput && /app/.venv/bin/daphne -b 0.0.0.0 -p $PORT Control_de_Venta.asgi:application"


