"""Gunicorn Configuration file. Stores required configuration to start Downloader Application"""
workers = 2
# 0.0.0.0 required for to make Application outside Container
bind = "0.0.0.0:80"
# default application variable
wsgi_app = "allocation.entrypoints.app:create_app()"
