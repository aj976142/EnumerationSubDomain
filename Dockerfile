FROM ubuntu

ENV THREAD_COUNT    200
ENV START_TIME      02:00
ENV MONITOR_FILE    monitor.txt
ENV DOMAINS_FILE    domains.txt
ENV DICT_FILE       subdomains.txt

RUN apt update && apt install python python-pip && rm -rf /var/lib/apt/lists/* && pip install dnspython gevent requests pyyaml pytz

CMD python enum_domains.py -f $DOMAINS_FILE -t $THREAD_COUNT -df $DICT_FILE -mf $MONITOR_FILE --start-time='$START_TIME' -e
