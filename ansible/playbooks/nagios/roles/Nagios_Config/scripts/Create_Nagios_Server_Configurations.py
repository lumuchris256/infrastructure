#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import os
import subprocess
import sys
from os import path
from jinja2 import Environment, FileSystemLoader

import yaml
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

# Parameter Definitions
Input_Path = sys.argv[1]
Output_Path = sys.argv[2]
Nagios_Service_Types = sys.argv[3]
Overwrite_Mode = sys.argv[4]

# Template Assignments
environment = Environment(loader=FileSystemLoader("templates/"))

# Import Configuration
import config
templates = config.templates
excluded_hosts = config.excluded_hosts

def main():

    # load config file for special cases
    config = configparser.RawConfigParser()
    config.read('ansible.cfg')

    # load public inventory
    basepath = path.dirname(__file__)
    inventory_path = Input_Path
    export = parse_yaml(load_yaml_file(inventory_path), config)



def load_yaml_file(file_name):
    """Loads YAML data from a file"""

    hosts = {}

    # get inventory
    with open(file_name, 'r') as stream:
        try:
            hosts = yaml.safe_load(stream)

        except yaml.YAMLError as exc:
            print(exc)
        finally:
            stream.close()

    return hosts


def parse_yaml(hosts, config):
    """Parses host information from the output of yaml.safe_load"""
    export = {'_meta': {'hostvars': {}}}

    for host_types in hosts['hosts']:
        for host_type, providers in host_types.items():
            export[host_type] = {}
            export[host_type]['hosts'] = []

            key = '~/.ssh/id_rsa'
            export[host_type]['vars'] = {
                'ansible_ssh_private_key_file': key
            }

            for provider in providers:
                for provider_name, hosts in provider.items():
                    # print (provider_name)  # print (hosts) # print (provider_name[ip])
                    for host, metadata in hosts.items():
                        # Get the IP From metadata
                        for i in metadata:
                            # Assign IP To Variable
                              if i == "ip":
                                 host_ip = metadata[i]

                        # some hosts have metadata appended to provider
                        # which requires underscore
                        # print(host_type,'-',provider_name,'-',host)
                        delimiter = "_" if host.count('-') == 3 else "-"
                        hostname = '{}-{}{}{}'.format(host_type, provider_name, delimiter, host)
                        # print("Hostname = "+hostname) # print("Host IP: = "+host_ip)
                        export[host_type]['hosts'].append(hostname)
                        # hostvars = {}

                        service_list = Nagios_Service_Types.split(" ")

                        matched_list=[]
                        unmatched_list=[]

                        for service in service_list:
                            if host_type == service:
                                formatted_name = host_type+'-'+provider_name+'-'+host
                                templated_name = host_type+'_'+host

                                if formatted_name not in (excluded_hosts):
                                    for key,value in templates.items():
                                        if templated_name.startswith(key):
                                            matched_list += [formatted_name]

                                    ## Check List Of Matched Hosts
                                    if formatted_name in matched_list:
                                        for key in templates:
                                            if templated_name.startswith(key):
                                                # print(formatted_name) # print(key, '->', templates[key])
                                                print("Name = "+formatted_name+" Template = "+templates[key]+" IP = "+host_ip)
                                                template_name=str(templates[key])
                                                template = environment.get_template(template_name)

                                                filepath = Output_Path+'/'+formatted_name+'.cfg'
                                                if os.path.isfile(Output_Path+'/'+formatted_name+'.cfg'):
                                                     ## Only Create File If Overwrite Is True
                                                     if OverWrite is True:
                                                         print("Overwrite")
                                                         with open(f"{Output_Path}/{formatted_name}.cfg", "w") as f:
                                                             ## Render J2 Template
                                                             content = template.render(
                                                             host_name = formatted_name,
                                                             host_ip_address = host_ip)
                                                             #  print(content)
                                                             f.write(f"{content}")
                                                             f.close()
                                                     else:
                                                        print("Will Not Overwrite :"+filepath)
                                                else:
                                                     print("Doesnt Exist - Create File")
                                                     with open(f"{Output_Path}/{formatted_name}.cfg", "w") as f:
                                                         ## Render J2 Template
                                                         content = template.render(
                                                         host_name = formatted_name,
                                                         host_ip_address = host_ip)
                                                         #  print(content)
                                                         f.write(f"{content}")
                                                         f.close()
                                    else:
                                        ## Deal With No Matching template
                                        print("No Matching Template For Hostname = "+hostname)
                                else:
                                    print("Excluded Host = "+formatted_name)

if __name__ == "__main__":

    main()