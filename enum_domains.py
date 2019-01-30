#!/usr/bin/env python
#coding=utf-8

import argparse
import gevent
import re
import random
import dns.resolver
import dns.zone
import sys
import time
import requests
import pytz
import datetime
import os
import smtplib
import yaml
import chardet

from difflib import SequenceMatcher
from email.mime.text import MIMEText
from urllib3.exceptions import NewConnectionError
from gevent import monkey
from gevent.queue import LifoQueue
monkey.patch_all()

class EnumerationSubDomain:

    def __init__(self, sub_dicts_file, domain=None, dns_server=None, coroutine_count=200, is_loop_query=True,
            out_file=None, domains_file=None, start_filter=True, start_time=None, monitor_file=None,
            send_email=False, loop_dict_file=None):
        if domain == None and domains_file == None:
           self.raise_error('must set domain or domains_file! use -d or -f args!')
        elif domain and domains_file:
           self.raise_error('-d and -f can only set one of the parameters') 
        
        # current domain to enumerate
        self.domain = domain
        # domains list to enumerate
        self.domains = []
        if domain:
            self.domains.append(domain)
        self.domains_file = domains_file
        # sub domain dict 
        self.sub_dicts = []
        self.sub_dicts_file = sub_dicts_file
        self.loop_sub_dicts = []
        self.loop_dict_file = loop_dict_file
        self.dns_server = dns_server
        self.dns_servers = ['114.114.114.114']
        # the result of enumerate
        # {'qq.com':['title':'qq','ips':['111.161.64.48', '111.161.64.40']]}
        self.domain_dict = {}
        # Coroutine count
        self.coroutine_count = coroutine_count
        self.is_loop_query = is_loop_query
        self.out_file = out_file
        self.tasks_queue = None
        self.new_found_domain_set = set()

        self.invalid_ip = ['0.0.0.1']
        self.is_dns_transfer = False
        self.is_wildcard = False
        self.wildcard_html = ''
        self.wildcard_html_len = 0
        self.similarity_rate = 0.8
        self.start_filter = start_filter
        self.config = None

        self.start_time = start_time
        self.send_email = send_email
        self.monitor_file = monitor_file
        self.monitor_domains = []
        if self.start_time:
            if self.monitor_file == None:
                self.raise_error('please set the -mf args while use --start-time args!')
            self.check_time_format(self.start_time)

        self.last_domains = self.domains
        self.current_domains = []
        # last query domain count
        self.last_query_count = 0
        # current query domain count
        self.current_query_count = 0

    def load_config(self):
        with open('config.yaml', 'r') as f:
            config = yaml.load(f)
        return config

    def raise_error(self, msg):
        raise RuntimeError(str(msg))

    def check_time_format(self,start_time):
        time_pattern = r'^\d\d:\d\d$'
        pattern = re.compile(time_pattern)
        if pattern.match(start_time):
            hour = int(start_time.split(':')[0])
            minute = int(start_time.split(':')[1])
            if (hour >= 0 and hour <=23) and (minute >= 0 and minute <=59):
                self.print_msg('tasks will start at %s' % start_time)
            else:
                raise RuntimeError('start_time format is wrong ! please use 01:02 or 22:30')
        else:
            raise RuntimeError('start_time format is wrong ! please use 01:02 or 22:30')

    def no_repeat_not_sort(self, lists):
        return list(set(lists))

    def no_repeat_sort(self, lists):
        result = list(set(lists))
        result.sort()
        return result

    def load_domains_from_file(self, file_name):
        domains = []
        lines = []
        with open(file_name, 'r') as f:
            lines = f.readlines()
        for line in lines:
            lists = line.split(',')
            domain = lists[0].strip()
            domains.append(domain)
        domains = self.no_repeat_not_sort(domains)
        return domains


    def init_monitor(self, monitor_file):
        monitor_domains = self.load_domains_from_file(monitor_file)
        return monitor_domains

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
        sys.stdout.write('[+] ' + msg.encode('utf-8') + '\n')

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
                self.print_msg('%s not a domain' % domain)
                return []
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

    def change_utf8(self, text):
        result = chardet.detect(text)
        charset = result['encoding']
        text = text.encode('utf-8')
        return text

    def get_title_from_html(self, html):
        title = ''
        title_patten = r'<title>(\s*?.*?\s*?)</title>'
        result = re.findall(title_patten, html)
        if len(result) >= 1:
            title = result[0]
            title = title.strip()
        # title = self.change_utf8(title)
        return title

    def improve_dicts(self, domains):
        self.add_sub_to_dicts(domains, 'mydict.txt')
        self.add_sub_to_dicts(domains, 'subdomains.txt')

    def get_domains_list(self):
        return self.domain_dict.keys()

    def concurrent_get_infos(self):
        info_tasks = []
        info_task_queue = self.init_tasks_queue(self.get_domains_list())
        coroutine_count = self.coroutine_count/4
        if coroutine_count < 20:
            coroutine_count = 20
        for i in range(coroutine_count):
            info_tasks.append(gevent.spawn(self.get_infos, info_task_queue))
        gevent.joinall(info_tasks)


    def do_concurrent_query(self, domain, sub_dicts):
        self.is_wildcard_resovler(domain) 
        transfer_domains = self.dns_transfer(domain)

        start_time = time.time()
        sub_domains = self.generate_sub_domains(domain, sub_dicts)
        if len(transfer_domains) > 0:
            sub_domains.extend(transfer_domains)
            sub_domains = self.no_repeat_not_sort(sub_domains)

        self.tasks_queue = self.init_tasks_queue(sub_domains)
        tasks = []
        for i in range(self.coroutine_count):
            tasks.append(gevent.spawn(self.concurrent_query, self.tasks_queue))
        gevent.joinall(tasks)
        end_time = time.time()
        total_time = int(end_time - start_time)
        self.print_msg('enumerate %d sub domain ! use %d coroutine ! The time used is %d seconds!' % (len(sub_domains), self.coroutine_count, total_time))

        if not self.is_wildcard:
            self.concurrent_get_infos()

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
                if self.loop_dict_file:
                    self.do_concurrent_query(domain, self.loop_sub_dicts)
                else:
                    self.do_concurrent_query(domain, self.sub_dicts)

            self.current_query_count = len(self.domain_dict)
    
    def write_domains_result_to_file(self, domain_names, file_name):
        with open(file_name,'w') as f:
            for domain in self.domains:
                for sub_domain in domain_names:
                    if sub_domain.endswith(domain):
                        sub_domain = sub_domain.encode('utf-8')
                        comma = ' , '
                        title = self.get_title_for_domain(sub_domain)
                        title = title.encode('utf-8')
                        line = sub_domain + comma + title + comma + comma.join(self.get_ips_for_domain(sub_domain)) + '\n'
                        f.write(line)
        self.print_msg('all sub domain write to %s !' % file_name)

    def append_domains_result_to_file(self, domain_names, file_name):
        with open(file_name,'a') as f:
            for domain in self.domains:
                for sub_domain in domain_names:
                    if sub_domain.endswith(domain):
                        sub_domain = sub_domain.encode('utf-8')
                        comma = ' , '
                        title = self.get_title_for_domain(sub_domain)
                        title = title.encode('utf-8')
                        line = sub_domain + comma + title + comma + comma.join(self.get_ips_for_domain(sub_domain)) + '\n'
                        f.write(line)
        self.print_msg('all %d sub domain append to %s !' % (len(domain_names), file_name))

    def write_sub_domains_to_file(self, file_name):
        if file_name == None:
            if self.domains_file:
                file_name = self.domains_file + self.get_current_time_str() + '.txt'
            else:
                file_name = self.domain + self.get_current_time_str() + '.txt'
        domain_names = self.domain_dict.keys()
        if os.path.exists(file_name):
            old_domain_names = self.load_domains_from_file(file_name)
            old_domain_names_set = set(old_domain_names)
            new_domains = []
            for domain in domain_names:
                if domain not in old_domain_names_set:
                    new_domains.append(domain)
            self.append_domains_result_to_file(new_domains, file_name)
        else:
            domain_names.sort()
            self.write_domains_result_to_file(domain_names, file_name)


    def get_current_time_str(self):
        timezone = pytz.timezone('Asia/Shanghai')
        now = datetime.datetime.now(timezone)
        time_str = '%.2d%.2d%.2d%.2d%.2d%.2d' % (now.year, now.month, now.day,
                now.hour, now.minute, now.second)
        return time_str

    def dns_transfer(self, domain):
        domains = []
        try:
            answers = self.dns_query(domain, 'NS')
            if answers:
                ns_servers = []
                for answer in answers:
                    ns_servers.append(str(answer))
                self.print_msg('ns_servers: %s' % str(ns_servers))
                ns_servers_ips = []
                for ns_server in ns_servers:
                    a_answers = self.dns_query(ns_server, 'A')
                    if a_answers:
                        for a_answer in a_answers:
                            ns_servers_ips.append(a_answer.address)
                self.print_msg('ns_servers_ips: %s' % str(ns_servers_ips))
                for ns_servers_ip in ns_servers_ips:
                    try:
                        zones = dns.zone.from_xfr(dns.query.xfr(ns_servers_ip, domain, relativize=False, timeout=2, lifetime=2), check_origin=False)
                        domain_names = zones.nodes.keys()
                        for domain_name in domain_names:
                            domain_name = str(domain_name)
                            domain_name = domain_name[:-1]
                            domains.append(domain_name)
                    except Exception as e:
                        self.print_msg(str(e))
                if len(domains) > 0:
                    self.print_msg('find dns transfer domains: %s !' % str(domains))
        except Exception as e:
            self.print_msg(str(e))
        if len(domains) > 0:
            self.is_dns_transfer = True
            self.print_msg('domain vuln to dns transfer!')
        else:
            self.print_msg('domain not vuln to dns transfer!')
        return domains

    def dns_query(self, domain, query_type='A'):
        resolver = dns.resolver.Resolver()
        resolver.nameservers = self.dns_servers
        answers = None
        try:
            answers = resolver.query(domain, query_type)
        except Exception as e:
            pass
        return answers

    def get_html_from_domain(self, domain):
        html = ''
        try:
            url = 'http://' + domain
            response = requests.get(url, timeout=3)
            html = response.content
            charset = chardet.detect(html)
            charset = charset['encoding']
            # self.print_msg('domain %s charset is %s, check charset is %s' % (domain, response.encoding, charset))
            response.encoding = charset
            html = response.text
            html.encode('utf-8')
        except NewConnectionError as e:
            if self.tasks_queue:
                self.tasks_queue.put(domain)
        except Exception as e:
            pass
            # self.print_msg('domain %s has error! %s' % (domain, str(e)))
        return html

    def wildcard_query(self, domain):
        domain_html = self.get_html_from_domain(domain)
        if domain_html:
            title = self.get_title_from_html(domain_html)
            if self.start_filter and self.check_filter(domain_html):
                self.print_msg('domain %s match filter %s, pass!' % (domain, title))
                return

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
                        self.set_ips_for_domain(domain, ips)
                        self.set_title_for_domain(domain, title)
                        # get more domain
                        domains = self.get_all_domains_from_html(self.domain, domain_html)
                        for domain in domains:
                            self.tasks_queue.put(domain)
                        domain = domain.encode('utf-8')
                        dns_server = self.dns_servers[0]
                        dns_server = dns_server.encode('utf-8')
                        self.print_msg('dns_server:%s, domain: %s , ips:%s, title: %s, html len %d' % (dns_server,  domain, str(ips), title, domain_html_len))
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
        answers = self.dns_query(domain, 'A')
        if answers:
            ips = self.get_ip_from_answers(answers)
            if len(ips) >= 1:
                self.set_ips_for_domain(domain, ips)
                self.print_msg('dns_server:%s, domain: %s , ips:%s' % (self.dns_servers[0], domain, str(ips)))
        self.cname_query(domain)

    def is_wildcard_resovler(self, domain):
        sub = self.get_current_time_str()
        not_exist_domain = sub + '.' + domain
        answers = self.dns_query(not_exist_domain)
        result = False
        if answers:
            self.wildcard_html = self.get_html_from_domain(not_exist_domain)
            self.wildcard_html_len = len(self.wildcard_html)
            if self.wildcard_html_len == 0:
                self.is_wildcard = False
                self.print_msg('%s is not wildcard !' % domain)
            else:
                self.is_wildcard = True
                result = True
                self.print_msg('%s is wildcard !' % domain)
                self.print_msg('len of wildcard html is %d !' % self.wildcard_html_len) 
        else:
            self.is_wildcard = False
            self.print_msg('%s is not wildcard !' % domain)
        return result

    def send_result_to_email(self, content, send_count=0):
        host = self.config['email_host']
        port = self.config['email_port']
        username = self.config['email_username']
        password = self.config['email_password']
        sender = self.config['email_sender']
        receiver = self.config['email_receiver']

        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = sender
        message['To'] = receiver
        message['Subject'] = 'the ' + self.get_current_time_str() + ' domain result'
        try:
            smtp_client = smtplib.SMTP_SSL(host, port, timeout=5)
            smtp_client.login(username, password)
            smtp_client.sendmail(sender, receiver, message.as_string())
            smtp_client.quit()
            self.print_msg('send email to %s success!' % receiver)
        except smtplib.SMTPException as e:
            self.print_msg(str(e))
            self.print_msg('Please make sure to fill in the correct configuration file email.yaml')
            self.send_result_to_email(content, send_count + 1)
        except Exception as e:
            self.print_msg(str(e))
            if send_count <= 5:
                self.send_result_to_email(content, send_count + 1)

    def make_content_for_domain(self, domain):
        content = ''
        content += '%s , title: %s , ips: %s' % (domain,self.get_title_for_domain(domain), str(self.get_ips_for_domain(domain)))
        content += '\n'
        return content

    def make_email_content(self, new_domains, found_domains):
        new_domains_count = len(new_domains)
        total_domains_count = len(found_domains)
        content = 'the result of ' + self.get_current_time_str() + '\n'
        content += 'found %d domain, found %d new domain\n' % (total_domains_count, new_domains_count)
        for domain in new_domains:
            content += self.make_content_for_domain(domain)
        content += 'all domains as follow: \n'
        for domain in found_domains:
            content += self.make_content_for_domain(domain)
        return content

    def set_ips_for_domain(self, domain, ips):
        '''
        domain_result = {
            'ips' : [127.0.0.1]
            'title' : 'XXX Login'
        }
        '''
        domain_result = {}
        if self.domain_dict.has_key(domain):
            domain_result = self.domain_dict[domain]
        domain_result['ips'] = ips
        self.domain_dict[domain] = domain_result
    
    def set_title_for_domain(self, domain, title):
        domain_result = {}
        if self.domain_dict.has_key(domain):
            domain_result = self.domain_dict[domain]
        domain_result['title'] = title
        self.domain_dict[domain] = domain_result

    def get_ips_for_domain(self, domain):
        if self.domain_dict.has_key(domain):
            domain_result = self.domain_dict[domain]
            ips = domain_result['ips']
            return ips
        else:
            return []

    def get_title_for_domain(self, domain):
        title = ''
        if self.domain_dict.has_key(domain):
            domain_result = self.domain_dict[domain]
            if domain_result.has_key('title'):
                title = domain_result['title']
        return title

    def get_all_domains_from_html(self, domain, html):
        domain_pattern = r'(?:[a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+' + domain
        pattern = re.compile(domain_pattern)
        domains = pattern.findall(html)
        domains = self.no_repeat_sort(domains)
        new_domains = []
        for domain in domains:
            if not domain in self.new_found_domain_set:
                new_domains.append(domain)
                self.new_found_domain_set.add(domain)
        if len(new_domains) > 0:
            self.print_msg('find new domains in html : %s' % str(new_domains))
        return new_domains

    def check_filter(self, html):
        title_filters = self.config['title_filters']
        html_filters = self.config['html_filters']
        result = False
        title = self.get_title_from_html(html)
        if len(title_filters) > 0:
            for f in title_filters:
                if f in title:
                    result =  True
                    break
        if len(html_filters) > 0:
            for f in html_filters:
                if f in html:
                    result = True
                    break
        return result

    def domain_has_title(self, domain):
        result = False
        domain_result = self.domain_dict[domain]
        if domain_result.has_key('title'):
            result = True
        return result

    def get_infos(self, tasks_queue):
        while not tasks_queue.empty():
            domain = tasks_queue.get()
            title = self.get_title_for_domain(domain)
            if not self.domain_has_title(domain):
                html = self.get_html_from_domain(domain)
                title = self.get_title_from_html(html)
                if self.start_filter and self.check_filter(html):
                    self.print_msg('domain %s match filter %s, pass!' % (domain, title))
                    self.domain_dict.pop(domain)
                else:
                    self.set_title_for_domain(domain, title)
                    self.print_msg('get %s domain title ok! title:%s' % (domain, title))

    def init_query(self):
        self.domain_dict = {}
        self.sub_dicts = self.load_sub_dicts(self.sub_dicts_file)
        self.loop_sub_dicts = self.load_sub_dicts(self.loop_dict_file)
        if self.domains_file:
            self.domains = self.load_domains_from_file(self.domains_file)
        if self.start_time:
            self.monitor_domains = self.init_monitor(self.monitor_file)
        if self.dns_server:
            self.dns_servers = [self.dns_server]
        else:
            self.dns_servers = self.auto_select_dns_server()
        self.config = self.load_config()

    def start(self):
        self.init_query() 

        start = time.time()
        for domain in self.domains:
            self.domain = domain
            self.do_concurrent_query(domain, self.sub_dicts)
        if self.is_loop_query:
            self.loop_query()

        end = time.time()
        total_time = int(end - start)
        self.print_msg('found %d sub domain ! The time used is %d seconds!' % (len(self.domain_dict), total_time))
        
        self.write_sub_domains_to_file(self.out_file)

        if self.start_time:
            monitor_domains_set = set(self.monitor_domains)
            found_domains = self.get_domains_list()
            found_domains_set = set(found_domains)
            new_domains = list(found_domains_set - monitor_domains_set)
            new_domains.sort()
            found_domains.sort()
            self.print_msg('find new %d domains: %s' % (len(new_domains), str(new_domains)))
            content = self.make_email_content(new_domains, found_domains)
            if self.is_dns_transfer:
                dns_transfer_str = 'domain has dns transfer vuln!\n'
                content = dns_transfer_str + content
            time_str = 'time use is %d second!\n' % total_time 
            content = time_str + content
            self.send_result_to_email(content)
            self.write_sub_domains_to_file(self.monitor_file)
        elif self.send_email:
            domains = self.get_domains_list()
            content = self.make_email_content([], domains)
            if self.is_dns_transfer:
                dns_transfer_str = 'domain has dns transfer vuln!\n'
                content = dns_transfer_str + content
            time_str = 'time use is %d second!\n' % total_time 
            content = time_str + content
            self.send_result_to_email(content)

    def enumerate(self):
        self.start()

        if self.start_time:
            while True:
                now_time_str = self.get_current_time_str()
                hour = now_time_str[8:10]
                minute = now_time_str[10:12]
                current_time = hour + ':' + minute
                if current_time == self.start_time:
                    self.print_msg('start now task!!!')
                    self.start()
                else:
                    self.print_msg('new task will start at %s current time is %s' % (self.start_time, current_time))
                    self.print_msg('wait one minute!')
                    time.sleep(60)

def parse_args():
    parser = argparse.ArgumentParser(description='A tool that can enumerate subdomains and support enumeration of subdomains above level 3')
    parser.add_argument('-d','--domain', metavar='qq.com', dest='domain', type=str, help=u'domain to enumeration. if use -f, don\'t need to set this arg.')
    parser.add_argument('-df','--dict-file',metavar='subnames.txt',dest='dict_file', type=str, default='subdomains.txt', help=u'Subdomain dictionary')
    parser.add_argument('-o','--out-file',metavar='domain.txt',dest='out_file', type=str, help=u'the file to write the result')
    parser.add_argument('-f','--domains-file',metavar='domains.txt',dest='domains_file', type=str, help=u'Read the domain name to be enumerated from this file')
    parser.add_argument('-nf', '--no-filter', dest='start_filter',action='store_false', default=True, help=u'filter to skip domain\' html match this string')
    parser.add_argument('--start-time',metavar=u'21:50',dest='start_time', type=str, help=u'time to start enumerate in every day !')
    parser.add_argument('-mf', '--monitor-file',metavar=u'monitor.txt',dest='monitor_file', type=str, help=u'the file store domains to monitor!')
    parser.add_argument('-ld', '--loop-dict',metavar=u'small_dicts.txt',dest='loop_dict_file', type=str, default='mydict.txt', help=u'the file store domains to monitor!')
    parser.add_argument('-t','--thread',metavar='200',dest='coroutine_count', type=int, default=200, help=u'the count of thread')
    parser.add_argument('-l','--loop', dest='is_loop_query', action='store_true', default=False, help=u'Whether to enable circular query')
    parser.add_argument('-e','--send-email', dest='send_email', action='store_true', default=False, help=u'Whether to send email, the config in email.yaml')
    parser.add_argument('--dns-server', metavar='8.8.8.8', dest='dns_server', type=str, help=u'dns server')
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
   dns_server = args.dns_server
   out_file = args.out_file
   domains_file = args.domains_file
   start_filter = args.start_filter
   start_time = args.start_time
   monitor_file = args.monitor_file
   loop_dict_file = args.loop_dict_file
   send_email = args.send_email
   enum_subdomain = EnumerationSubDomain(sub_dicts_file, domain, coroutine_count=coroutine_count, is_loop_query=is_loop_query,
               dns_server=dns_server, out_file=out_file, domains_file=domains_file, start_filter=start_filter,
               start_time=start_time, monitor_file=monitor_file, send_email=send_email, loop_dict_file=loop_dict_file)
   try:
       enum_subdomain.enumerate()
   except KeyboardInterrupt as e:
       enum_subdomain.print_msg('user abort !')
       enum_subdomain.write_sub_domains_to_file(out_file)
       enum_subdomain.improve_dicts(enum_subdomain.get_domains_list())

if __name__ == '__main__':
    main()
