#! /bin/bash 

source ../bin/activate
gunicorn MiRA.wsgi:application -c gunicorn.conf.py
