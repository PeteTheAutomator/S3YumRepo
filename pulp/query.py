#!/usr/bin/env python

import requests
import json
import argparse
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def argumentparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", type=str, help="server hostname or ip address", required=True)
    parser.add_argument("-u", "--user", type=str, help="username credential", required=True)
    parser.add_argument("-p", "--password", type=str, help="password credential", required=True)
    parser.add_argument("-c", "--channel", type=str, help="satellite channel id", required=True)
    args = parser.parse_args()
    return vars(args)


class Query:
    def __init__(self, server, user, password, channel):
        self.creds = (user, password)
        self.server = server
        self.channel = channel

    def get_repo(self):
        r = requests.get('https://' + self.server + '/pulp/api/v2/repositories/' + self.channel + '/', auth=self.creds, verify=False, params={'distributors':'True'})
        d = json.loads(r._content)
        return d

    def get_repo_relative_url(self, repo):
        for distributor in repo['distributors']:
            if distributor['id'] == 'yum_distributor':
                relative_url = distributor['config']['relative_url']

        return relative_url

    def get_packages(self):
        query = {'criteria':{'fields':{'unit':['name','version']},'type_ids':['rpm'],'limit':100}}
        query_json = json.dumps(query)
        r = requests.post('https://' + self.server + '/pulp/api/v2/repositories/' + self.channel + '/search/units/', data=query_json, auth=self.creds, verify=False)
        d = json.loads(r._content)
        return d

    def get_package_metadata(self, unit_id):
        r = requests.get('https://' + self.server + '/pulp/api/v2/content/units/rpm/' + unit_id + '/', auth=self.creds, verify=False)
        d = json.loads(r._content)
        return d


if __name__ == "__main__":
    args = argumentparser()
    server = args['server']
    user = args['user']
    password = args['password']
    channel = args['channel']

    q = Query(server, user, password, channel)

    repo = q.get_repo()
    relative_url = q.get_repo_relative_url(repo)

    results = {}
    results['repo'] = repo['id']
    results['checksum_type'] = repo['scratchpad']['checksum_type']
    results['packages'] = []

    packages = q.get_packages()

    for package in packages:
        metadata = q.get_package_metadata(package['unit_id'])
        url = 'https://' + server + '/pulp/repos/' + relative_url + metadata['filename']
        checksum = metadata['checksum']
        results['packages'].append({'url': url, 'checksum': checksum})

    print json.dumps(results, indent=4)
