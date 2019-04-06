#!/usr/bin/python
# -*- coding: utf-8 -*-
# borrow code from https://github.com/patrickwangqy/AutoUpdateDomain.git
# whith modify by hjm
from QcloudApi.qcloudapi import QcloudApi
import requests
import json
import os
import datetime
import time
import argparse
import sys
reload(sys) 
sys.setdefaultencoding('utf8') 
#get your true IP
def get_out_ip():
    session = requests.Session()
    session.trust_env = False
    response = session.get('http://ifconfig.co/ip')
    myip = response.text.strip()
    return "%s" % myip


#refer to https://github.com/QcloudApi/qcloudapi-sdk-python
def get_cns_service(secretId,secretKey):
    module = 'cns'
    config = {
        'Region': 'ap-beijing',
        'secretId':secretId,
        'secretKey':secretKey,
        'method': 'get'
    }
    service = QcloudApi(module, config)
    return service

#refers to https://cloud.tencent.com/document/api/302/8517
def get_record_list(cns_service,domain):
    action = 'RecordList'
    params = {
        'domain':domain,
    }
    return cns_service.call(action, params)
#refers to https://cloud.tencent.com/document/api/302/8516
def add_dns_record_ip(cns_service,domain,subdomain,ip):
    action = 'RecordCreate'
    params = {
        'domain':domain,
        'subDomain':subdomain,
        'recordLine':'默认',
        'recordType':'A',
        'value':ip,
    }
    return cns_service.call(action,params)

#refers to https://cloud.tencent.com/document/api/302/8511
def modify_dns_record_ip(cns_service,domain,subdomain,record_id,ip):
    action = 'RecordModify'
    params = {
        'domain':domain,
        'subDomain':subdomain,
        'recordId':record_id,
        'recordLine':'默认',
        'recordType':'A',
        'value':ip,
    }
    print(params)
    return cns_service.call(action,params)
def monitor_domain(my_domain, my_subdomain, my_secret_id, my_secret_key,my_ip):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    #Need reqeust in https://console.cloud.tencent.com/capi
    secretId = my_secret_id
    secretKey = my_secret_key

    #buy domain name in https://dnspod.cloud.tencent.com/?from=qcloudProductDns
    domain = my_domain
    subdomain = my_subdomain
    if my_ip == "0.0.0.0":
        ip = get_out_ip()
    else:
        ip = my_ip
    print("my outbind ip: "+ip)
    OUT_IP_FILE = './out_ip.txt'

    if not os.path.exists(OUT_IP_FILE):
        with open(OUT_IP_FILE,'w+') as f:
            f.write(ip)
            print("[dns_tool]:Cache IP:{} as file".format(ip))
    else:
        with open(OUT_IP_FILE,'r+') as f:
            old_ip = f.read()
            if old_ip == ip:
                print("[dns_tool]:not need update,current IP:"+old_ip)

            else:
                f.seek(0)
                f.truncate(0)
                f.write(ip)
                print("[dns_tool]:Update a IP:{},old ip: {}".format(ip,old_ip))

    service = get_cns_service(secretId,secretKey)
    record_list = json.loads(get_record_list(service,domain))
    json.dumps(record_list)

    is_ip = False
    record_id = 0
    for item in record_list["data"]["records"]:
        if item["type"] == 'A' and item["name"] == subdomain:
            is_ip = True
            record_id = item["id"]
            modify_dns_record_ip(service, domain, subdomain, record_id, ip)
            print("[dns_tool]:Modify a record, id: {}".format(record_id))
    if not is_ip:
        add_dns_record_ip(service, domain,subdomain, ip)
        print("[dns_tool]:Create a new ip record for domain: "+subdomain +"."+domain)

def main():
    default_secretid = os.environ.get("SECRETID", 'YOURsecretid')
    default_secretkey = os.environ.get("SECRETKEY", 'YOURsecretkey')
    parser = argparse.ArgumentParser()
    parser.add_argument("--access_key_id", type=str, default=default_secretid)
    parser.add_argument("--access_key_secret", type=str, default=default_secretkey)
    parser.add_argument("--domain", type=str, required=True)
    parser.add_argument("--subdomain", type=str, required=True)
    parser.add_argument("--ip", type=str, default="0.0.0.0")
    parser.add_argument("--sleep", type=int, default=5)
    args = parser.parse_args()
    while True:
        try:
            monitor_domain(args.domain, args.subdomain, args.access_key_id, args.access_key_secret, args.ip)
        except Exception as e:
            pass
        time.sleep(args.sleep)


if (__name__ == '__main__'):
    main()
