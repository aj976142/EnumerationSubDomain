FROM jfloff/alpine-python

RUN pip install dnspython gevent requests pyyaml pytz
