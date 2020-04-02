release: python manage.py migrate
release: python manage.py collectstatic
web: gunicorn config.wsgi --log-file -