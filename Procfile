web: cd trade_remedies_caseworker && python ./manage.py migrate && ./manage.py collectstatic --noinput && gunicorn config.wsgi --bind 0.0.0.0:8080 --capture-output --config config/gunicorn.py
