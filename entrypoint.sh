#!/usr/bin/env bash

set -e
set -x 

env
if [ "$1" == 'web' ] 
then
  if [ "$HLL_HOST" == '' ] 
  then
      exit 0
  fi
  alembic upgrade head
  ./manage.py init_db
  ./manage.py register_api
  cd rconweb 
  ./manage.py migrate --noinput
  ./manage.py collectstatic --noinput
  echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').first() else None" | python manage.py shell
  gunicorn -w $NB_API_WORKERS -t 120 -b 0.0.0.0 rconweb.wsgi
  cd ..
  ./manage.py unregister_api
else
if [ "$1" == 'debug' ] 
then
  tail -f manage.py
fi
if [ "$HLL_HOST" == '' ] 
then
    exit 0
fi
  sleep 10
  env >> /etc/environment
  supervisord -c /config/supervisord_$SERVER_NUMBER.conf || supervisord -c /config/supervisord.conf
fi

