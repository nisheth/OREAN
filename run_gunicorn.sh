#! /bin/bash 

source ../bin/activate
gunicorn OREAN.wsgi:application -c gunicorn.conf.py
