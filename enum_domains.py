#!/usr/bin/env python
#coding=utf-8

import argparse
import time
from EnumerationSubDomain import EnumerationSubDomain

def parse_args():
    parser = argparse.ArgumentParser(description='A tool that can enumerate subdomains and support enumeration of subdomains above level 3')
    parser.add_argument('-d','--domain', metavar='qq.com', dest='domain', type=str, required=True, help=u'domain to enumeration')
    parser.add_argument('-D','--dict',metavar='subnames.txt',dest='dict', type=str, default='subdomains.txt', help=u'Subdomain dictionary')
    parser.add_argument('-t','--thread',metavar='200',dest='coroutine_count', type=int, default=200, help=u'the count of thread')
    parser.add_argument('-n','--no-loop', dest='is_loop_query', action='store_false', default=True, help=u'Whether to enable circular query')
    args = parser.parse_args()
    return args

def get_dict_from_file(file_name):
    sub_dicts = []
    with open(file_name, 'r') as f:
        dicts = f.readlines()
        for sub in dicts:
            sub_dicts.append(sub.strip())
    return sub_dicts

def write_sub_domains_to_file(sub_domains, file_name):
    domain_names = sub_domains.keys()
    with open(file_name,'w') as f:
        for domain in domain_names:
            f.write(domain + ' , ' + ' , '.join(sub_domains[domain]) + '\n')
    print 'all sub domain write to %s !' % file_name


def main():
   args = parse_args()
   sub_dicts = get_dict_from_file(args.dict)
   domain = args.domain
   is_loop = args.is_loop_query
   count = args.coroutine_count
   enum_subdomain = EnumerationSubDomain(domain, sub_dicts, coroutine_count=count, is_loop_query=is_loop)
   sub_domains = enum_subdomain.enumerate()
   file_name = domain + time.strftime("_%Y%m%d%H%M%S", time.gmtime(time.time())) + '.txt'
   write_sub_domains_to_file(sub_domains, file_name)
   
if __name__ == '__main__':
    main()
