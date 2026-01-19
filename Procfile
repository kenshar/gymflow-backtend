release: python -m flask db upgrade
web: gunicorn --workers 4 --bind 0.0.0.0:$PORT run:app
