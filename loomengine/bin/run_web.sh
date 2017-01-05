#!/bin/bash

gunicorn ${SERVER_WSGI_MODULE} --bind ${BIND_IP}:${BIND_PORT} --pid ${WEBSERVER_PIDFILE} --access-logfile ${ACCESS_LOGFILE} --error-logfile ${ERROR_LOGFILE} --log-level ${LOG_LEVEL} --capture-output
