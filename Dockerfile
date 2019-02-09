FROM ubuntu

RUN apt update && apt install python python-pip -y && rm -rf /var/lib/apt/lists/* && pip install dnspython gevent requests pyyaml pytz
