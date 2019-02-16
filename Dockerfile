FROM jfloff/alpine-python:2.7

RUN pip install dnspython gevent requests pyyaml pytz
