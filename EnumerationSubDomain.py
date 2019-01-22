#!/usr/bin/env python
#coding=utf-8

import gevent
import re
import random
import dns.resolver
import sys
import time

from gevent import monkey
from gevent.queue import Queue
monkey.patch_all()

class EnumerationSubDomain:

    def __init__(self, domain, sub_dicts, dns_servers=None, coroutine_count=200, is_loop_query=True):
        self.domain = domain
        self.sub_dicts = sub_dicts
        self.sub_domains = self.generate_sub_domains(domain, sub_dicts)
        if dns_servers == None:
            self.dns_servers = self.auto_select_dns_server()
        else:
            self.dns_servers = [dns_servers]
        # {'qq.com':['111.161.64.48', '111.161.64.40']}
        self.domain_dict = {}
        # Coroutine count
        self.coroutine_count = coroutine_count
        self.is_loop_query = is_loop_query
        self.invalid_ip = ['0.0.0.1', '127.0.0.1']

        self.last_domains = [domain]
        self.current_domains = []
        # last query domain count
        self.last_query_count = 0
        # current query domain count
        self.current_query_count = 0

    def auto_select_dns_server(self):
        dns_servers = [
                '114.114.114.114',  # 114DNS
                 '223.5.5.5',  # AliDNS
                 '1.1.1.1',  # Cloudflare
                 '119.29.29.29',  # DNSPod
                 '1.2.4.8',  # sDNS
                 '8.8.8.8' # Google
                ]
        fast_dns_server_time = 1.0
        fast_dns_server = '' 
        for dns_server in dns_servers:
           resolver = dns.resolver.Resolver()
           resolver.nameservers = [dns_server]
           start_time = time.time()
           answer = resolver.query('baidu.com', 'A')
           end_time = time.time()
           total_time = end_time - start_time
           self.print_msg('dns_server: %s use %f to query ...' % (dns_server, total_time))
           if total_time < fast_dns_server_time:
               fast_dns_server = dns_server
               fast_dns_server_time = total_time
        self.print_msg('dns_server: %s is fast !' % fast_dns_server)
        return [fast_dns_server]

    def init_tasks_queue(self, sub_domains):
        tasks_queue = Queue()
        for sub_domain in sub_domains:
            tasks_queue.put(sub_domain)
        return tasks_queue

    def print_msg(self, msg):
        sys.stdout.write('[+] ' + str(msg) + '\n')

    def is_domain(self, domain):
        domain_pattern = r'^[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+$'
        pattern = re.compile(domain_pattern)
        if not pattern.match(domain):
            return False
        else:
            return True

    def generate_sub_domains(self, domain, sub_dicts):
        sub_dicts = list(set(sub_dicts))
        self.print_msg('load %d sub domain dicts ...' % len(sub_dicts))
        sub_domains = []
        if not self.is_domain(domain):
            raise RuntimeError('%s not a domain' % domain)
        sub_domains.append(domain)
        for sub in sub_dicts:
            sub_domain = sub + '.' + domain
            if self.is_domain(sub_domain):
                sub_domains.append(sub_domain)
        self.print_msg('generate %s sub domains with %s ...' % (len(sub_domains), domain))
        return sub_domains

    def query(self, domain):
        # dns_server = self.dns_servers[random.randint(0,len(self.dns_servers) - 1)]
        dns_server = self.dns_servers[0]
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        try:
            answers = resolver.query(domain, 'A')
            if answers:
                ips = []
                for answer in answers:
                    ip = answer.address
                    if ip in self.invalid_ip:
                        return
                    else:
                        ips.append(ip)
                ips.sort()
                self.domain_dict[domain] = ips
                self.print_msg('dns_server:%s, domain: %s , ips:%s' % (dns_server, domain, str(ips)))
        except Exception as e:
            # self.print_err('dns_server:%s, domain:%s, error:%s' % (dns_server, domain, str(e)))
            pass

    def print_err(self, msg):
        sys.stdout.write('[-] ' + str(msg) + '\n')

    def concurrent_query(self, tasks_queue):
        while not tasks_queue.empty():
            sub_domain = tasks_queue.get()
            self.query(sub_domain)

    def do_concurrent_query(self, sub_domains):
        start_time = time.time()
        tasks_queue = self.init_tasks_queue(sub_domains)
        tasks = []
        for i in range(self.coroutine_count):
            tasks.append(gevent.spawn(self.concurrent_query, tasks_queue))
        gevent.joinall(tasks)
        end_time = time.time()
        total_time = int(end_time - start_time)
        self.print_msg('enumerate %d sub domain ! use %d coroutine ! The time used is %d seconds!' % (len(self.sub_domains), self.coroutine_count, total_time))


    def loop_query(self):
        self.current_query_count = len(self.domain_dict)
        loop_count = 0
        while self.current_query_count > self.last_query_count:
            loop_count += 1
            self.print_msg('do %d loop query ...' % loop_count)
            self.current_domains = self.domain_dict.keys()
            # last_domains = ['qq.com']
            # current_domains = ['qq.com', 'www.qq.com', 'cn.qq.com']
            # query_domains = ['www.qq.com', 'cn.qq.com']
            # Use query_domains to enumerate domain names like 'm.cn.qq.com'
            query_domains = list(set(self.current_domains) - set(self.last_domains))
            self.print_msg('use %s to enumerate ...' % str(query_domains))

            self.last_domains = self.current_domains
            self.last_query_count = self.current_query_count

            self.sub_domains = []
            for domain in query_domains:
                tmp_domains = self.generate_sub_domains(domain, self.sub_dicts)
                tmp_domains.remove(domain)
                self.sub_domains.extend(tmp_domains)

            self.do_concurrent_query(self.sub_domains)

            self.current_query_count = len(self.domain_dict)

    def enumerate(self):
        start_time = time.time()
        self.do_concurrent_query(self.sub_domains)
        if self.is_loop_query:
            self.loop_query()

        end_time = time.time()
        total_time = int(end_time - start_time)
        self.print_msg('%s found %d sub domain ! The time used is %d seconds!' % (self.domain, len(self.domain_dict), total_time))
        return self.domain_dict

