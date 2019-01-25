#!/usr/bin/env python
#coding=utf-8

import argparse
import gevent
import re
import random
import dns.resolver
import sys
import time
import requests

from difflib import SequenceMatcher
from gevent import monkey
from gevent.queue import LifoQueue
monkey.patch_all()

class EnumerationSubDomain:

    def __init__(self, sub_dicts_file, domain=None, dns_servers=None, coroutine_count=200, is_loop_query=True,
            out_file=None, domains_file=None, filter_pattern=None):
        if domain == None and domains_file == None:
            raise RuntimeError('must set domain or domains_file! use -d or -f args!')

        self.domain = domain
        self.domains = []
        if domain:
            self.domains.append(domain)

        self.sub_dicts = self.load_sub_dicts(sub_dicts_file)
        if dns_servers == None:
            self.dns_servers = self.auto_select_dns_server()
        else:
            self.dns_servers = [dns_servers]
        # {'qq.com':['111.161.64.48', '111.161.64.40']}
        self.domain_dict = {}
        # Coroutine count
        self.coroutine_count = coroutine_count
        self.is_loop_query = is_loop_query
        self.out_file = out_file
        self.domains_file = domains_file
        self.load_sub_domains_from_file(self.domains_file)
        self.tasks_queue = None
        self.invalid_ip = ['0.0.0.1']
        self.is_wildcard = False
        self.wildcard_html = ''
        self.wildcard_html_len = 0
        self.similarity_rate = 0.8
        self.filter_pattern = filter_pattern
        if self.filter_pattern:
            self.filter_pattern = unicode(self.filter_pattern, 'utf-8')

        self.last_domains = [domain]
        self.current_domains = []
        # last query domain count
        self.last_query_count = 0
        # current query domain count
        self.current_query_count = 0

    def no_repeat_not_sort(self, lists):
        return list(set(lists))

    def no_repeat_sort(self, lists):
        result = list(set(lists))
        result.sort()
        return result

    def load_sub_domains_from_file(self, domains_file):
        if domains_file:
            with open(domains_file, 'r') as f:
                domains = f.readlines()
                for domain in domains:
                    domain = domain.strip()
                    self.domains.append(domain)
            self.domains = self.no_repeat_not_sort(self.domains)
    
    def load_sub_dicts(self, sub_dicts_file):
        sub_dicts = []
        with open(sub_dicts_file, 'r') as f:
            dicts = f.readlines()
            for sub in dicts:
                sub_dicts.append(sub.strip())
        return sub_dicts

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
           resolver.timeout = 1
           resolver.lifetime = 1
           start_time = time.time()
           try:
               answer = resolver.query('baidu.com', 'A')
           except Exception as e:
               pass
           end_time = time.time()
           total_time = end_time - start_time
           self.print_msg('dns_server: %s use %f to query ...' % (dns_server, total_time))
           if total_time < fast_dns_server_time:
               fast_dns_server = dns_server
               fast_dns_server_time = total_time
        self.print_msg('dns_server: %s is fast !' % fast_dns_server)
        return [fast_dns_server]

    def init_tasks_queue(self, sub_domains):
        tasks_queue = LifoQueue()
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
        if domain == None:
            return []
        else:
            sub_dicts = self.no_repeat_not_sort(sub_dicts)
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
    
    def get_ip_from_answers(self, answers):
        ips = []
        ip_pattern = r'^(127\.0\.0\.1)|(localhost)|(10\.\d{1,3}\.\d{1,3}\.\d{1,3})|(172\.((1[6-9])|(2\d)|(3[01]))\.\d{1,3}\.\d{1,3})|(192\.168\.\d{1,3}\.\d{1,3})$'
        pattern = re.compile(ip_pattern)
        for answer in answers:
            ip = answer.address
            if not pattern.match(ip) and ip not in self.invalid_ip:
                ips.append(ip)
        ips.sort()
        return ips

    def print_err(self, msg):
        sys.stdout.write('[-] ' + str(msg) + '\n')

    def concurrent_query(self, tasks_queue):
        while not tasks_queue.empty():
            sub_domain = tasks_queue.get()
            if self.is_wildcard:
                self.wildcard_query(sub_domain)
            else:
                self.query(sub_domain)

    def add_sub_to_dicts(self, domains, file_name):
        sub_list = []
        with open(file_name,'r') as f:
            sub_list = f.readlines()
        old_num = len(sub_list)
        for domain in domains:
            subs = domain.split('.')
            for sub in subs:
                sub_list.append(sub + '\n')
        sub_list = self.no_repeat_sort(sub_list)
        with open(file_name, 'w') as f:
            f.writelines(sub_list)
        new_num = len(sub_list)
        new_num = new_num - old_num
        self.print_msg('add %d new sub to %s ' % (new_num, file_name))

    def improve_dicts(self, domains):
        self.add_sub_to_dicts(domains, 'my_sub_dicts.txt')
        self.add_sub_to_dicts(domains, 'subdomains.txt')


    def get_domains_list(self):
        return self.domain_dict.keys()

    def do_concurrent_query(self, domain, sub_dicts):
        self.is_wildcard_resovler(domain) 

        start_time = time.time()
        sub_domains = self.generate_sub_domains(domain, sub_dicts)
        self.tasks_queue = self.init_tasks_queue(sub_domains)
        tasks = []
        for i in range(self.coroutine_count):
            tasks.append(gevent.spawn(self.concurrent_query, self.tasks_queue))
        gevent.joinall(tasks)
        end_time = time.time()
        total_time = int(end_time - start_time)
        self.print_msg('enumerate %d sub domain ! use %d coroutine ! The time used is %d seconds!' % (len(sub_domains), self.coroutine_count, total_time))
        self.improve_dicts(self.get_domains_list())

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

            for domain in query_domains:
                self.do_concurrent_query(domain, self.sub_dicts)

            self.current_query_count = len(self.domain_dict)

    def write_sub_domains_to_file(self):
        if self.out_file:
            file_name = self.out_file
        else:
            if self.domain:
                file_name = self.domain + self.get_current_time_str() + '.txt'
            else:
                file_name = self.domains_file + self.get_current_time_str() + '.txt'
        domain_names = self.domain_dict.keys()
        with open(file_name,'w') as f:
            for domain in self.domains:
                for sub_domain in domain_names:
                    if sub_domain.endswith(domain):
                        f.write(sub_domain + ' , ' + ' , '.join(self.domain_dict[sub_domain]) + '\n')
        self.print_msg('all sub domain write to %s !' % file_name)

    def get_current_time_str(self):
        return time.strftime("%Y%m%d%H%M%S", time.gmtime(time.time()))

    def dns_query(self, domain, query_type='A'):
        resolver = dns.resolver.Resolver()
        resolver.nameservers = self.dns_servers
        answers = None
        try:
            answers = resolver.query(domain, query_type)
        except Exception as e:
            answers = None
        return answers

    def get_html_from_domain(self, domain):
        html = ''
        try:
            url = 'http://' + domain
            response = requests.get(url, headers={"Connection": "close"})
            response.encoding = 'utf-8'
            html = response.text
        except Exception as e:
            if self.tasks_queue:
                self.tasks_queue.put(domain)
        return html

    def wildcard_query(self, domain):
        domain_html = self.get_html_from_domain(domain)
        if domain_html:
            domain_html_len = len(domain_html)
            if domain_html_len == self.wildcard_html_len:
                similarity_rate = 1.0
            else:
                similarity_rate = SequenceMatcher(None, domain_html, self.wildcard_html).real_quick_ratio()
                similarity_rate = round(similarity_rate, 3)
            if similarity_rate < self.similarity_rate:
                # exist sub domain
                answers = self.dns_query(domain)
                if answers:
                    ips = self.get_ip_from_answers(answers)
                    if len(ips) >= 1:
                        if self.filter_pattern in domain_html:
                            self.print_msg('%s domain match filter pass!' % domain)
                        else:
                            self.domain_dict[domain] = ips
                            self.print_msg('dns_server:%s, domain: %s , ips:%s, html len %d' % (self.dns_servers[0],  domain, str(ips), domain_html_len))
                self.cname_query(domain)
    
    def cname_query(self, domain):
        answers = self.dns_query(domain, 'CNAME')
        if answers:
            for answer in answers:
                cname_domain = answer.to_text()
                # music.tcdn.qq.com.
                cname_domain = cname_domain[:-1]
                if cname_domain.endswith(self.domain) and not self.domain_dict.has_key(cname_domain):
                    self.print_msg('find cname domain: %s ' % cname_domain)
                    self.tasks_queue.put(cname_domain)


    def query(self, domain):
        # dns_server = self.dns_servers[random.randint(0,len(self.dns_servers) - 1)]
        dns_server = self.dns_servers[0]
        answers = self.dns_query(domain, 'A')
        if answers:
            ips = self.get_ip_from_answers(answers)
            if len(ips) >= 1:
                self.domain_dict[domain] = ips
                self.print_msg('dns_server:%s, domain: %s , ips:%s' % (dns_server, domain, str(ips)))
        self.cname_query(domain)

    def is_wildcard_resovler(self, domain):
        sub = self.get_current_time_str()
        not_exist_domain = sub + '.' + domain
        answers = self.dns_query(not_exist_domain)
        if answers:
            self.is_wildcard = True
            print vars(answers)
            self.print_msg('%s is wildcard !' % domain)
            self.wildcard_html = self.get_html_from_domain(not_exist_domain)
            self.wildcard_html_len = len(self.wildcard_html)
            self.print_msg('len of wildcard html is %d !' % self.wildcard_html_len) 
            return True
        else:
            self.is_wildcard = False
            self.print_msg('%s is not wildcard !' % domain)
            return False

    def enumerate(self):

        start_time = time.time()
        for domain in self.domains:
            self.domain = domain
            self.do_concurrent_query(domain, self.sub_dicts)
        if self.is_loop_query:
            self.loop_query()

        end_time = time.time()
        total_time = int(end_time - start_time)
        self.print_msg('found %d sub domain ! The time used is %d seconds!' % (len(self.domain_dict), total_time))
        self.write_sub_domains_to_file()
        return self.domain_dict

def parse_args():
    parser = argparse.ArgumentParser(description='A tool that can enumerate subdomains and support enumeration of subdomains above level 3')
    parser.add_argument('-d','--domain', metavar='qq.com', dest='domain', type=str, help=u'domain to enumeration. if use -f, don\'t need to set this arg.')
    parser.add_argument('-df','--dict-file',metavar='subnames.txt',dest='dict_file', type=str, default='subdomains.txt', help=u'Subdomain dictionary')
    parser.add_argument('-o','--out-file',metavar='domain.txt',dest='out_file', type=str, help=u'the file to write the result')
    parser.add_argument('-f','--domains-file',metavar='domains.txt',dest='domains_file', type=str, help=u'Read the domain name to be enumerated from this file')
    parser.add_argument('--filter',metavar=u'xxx shop',dest='filter_pattern', type=str, help=u'filter to skip domain\' html match this string')
    parser.add_argument('-t','--thread',metavar='200',dest='coroutine_count', type=int, default=200, help=u'the count of thread')
    parser.add_argument('-n','--no-loop', dest='is_loop_query', action='store_false', default=True, help=u'Whether to enable circular query')
    parser.add_argument('--dns-server', metavar='8.8.8.8', dest='dns_servers', type=str, help=u'dns server')
    args = parser.parse_args()
    if args.domain == None and args.domains_file == None:
        parser.print_help()
        sys.exit()
    return args

def main():
   args = parse_args()
   sub_dicts_file = args.dict_file
   domain = args.domain
   is_loop_query = args.is_loop_query
   coroutine_count = args.coroutine_count
   dns_servers = args.dns_servers
   out_file = args.out_file
   domains_file = args.domains_file
   filter_pattern = args.filter_pattern

   enum_subdomain = EnumerationSubDomain(sub_dicts_file, domain, coroutine_count=coroutine_count, is_loop_query=is_loop_query,
               dns_servers=dns_servers, out_file=out_file, domains_file=domains_file, filter_pattern=filter_pattern)
   try:
       enum_subdomain.enumerate()
   except KeyboardInterrupt as e:
       enum_subdomain.print_msg('user abort !')
       enum_subdomain.write_sub_domains_to_file()
       enum_subdomain.improve_dicts(enum_subdomain.get_domains_list())

if __name__ == '__main__':
    main()
