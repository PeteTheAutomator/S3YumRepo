#!/usr/bin/env python

import requests
import json
import argparse
import urllib3
import hashlib
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def sha256(fname):
    hash_md5 = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def argumentparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", type=str, help="server hostname or ip address", required=True)
    parser.add_argument("-u", "--user", type=str, help="username credential", required=True)
    parser.add_argument("-p", "--password", type=str, help="password credential", required=True)
    parser.add_argument("-c", "--channel", type=str, help="satellite channel id", required=True)
    args = parser.parse_args()
    return vars(args)


class Repo:
    def __init__(self, server, user, password, channel):
        self.creds = (user, password)
        self.server = server
        self.channel = channel
        self.apibase = 'https://' + self.server + '/pulp/api/v2'
        self.repobase = 'https://' + self.server + '/pulp/repos/'
        self.metadata = {}

    def get(self):
        r = requests.get(self.apibase + '/repositories/' + self.channel + '/', auth=self.creds, verify=False,
                         params={'distributors': 'True'})
        self.metadata = json.loads(r._content)

    @property
    def packages(self):
        query = {'criteria': {'fields': {'unit': ['name', 'version']}, 'type_ids': ['rpm'], 'limit': 5}}
        query_json = json.dumps(query)
        r = requests.post(self.apibase + '/repositories/' + self.channel + '/search/units/', data=query_json,
                          auth=self.creds, verify=False)
        d = json.loads(r._content)
        return d

    @property
    def relative_url(self):
        for distributor in self.metadata['distributors']:
            if distributor['id'] == 'yum_distributor':
                relative_url = distributor['config']['relative_url']
                return relative_url
        return False


class RPM:
    def __init__(self, repo):
        self.repo = repo
        self.metadata = {}

    def get(self, unit_id):
        r = requests.get(self.repo.apibase + '/content/units/rpm/' + unit_id + '/', auth=self.repo.creds, verify=False)
        self.metadata = json.loads(r._content)

    @property
    def url(self):
        return r.repobase + r.relative_url + self.metadata['filename']

    def retrieve(self):
        r = requests.get(self.url, verify=False)
        open(self.metadata['filename'], 'wb').write(r.content)


if __name__ == "__main__":
    args = argumentparser()
    server = args['server']
    user = args['user']
    password = args['password']
    channel = args['channel']

    results = {}

    r = Repo(server, user, password, channel)
    r.get()

    results['repo'] = r.metadata['id']
    results['checksum_type'] = r.metadata['scratchpad']['checksum_type']
    results['packages'] = []

    for package in r.packages:
        rpm = RPM(r)
        rpm.get(package['unit_id'])
        results['packages'].append({'filename': rpm.metadata['filename'], 'checksum': rpm.metadata['checksum'],
                                    'url': rpm.url})

        # TODO: implement further checksum types
        checksum = None
        if os.path.exists(rpm.metadata['filename']):
            if r.metadata['scratchpad']['checksum_type'] == 'sha256':
                checksum = sha256(rpm.metadata['filename'])
            elif r.metadata['scratchpad']['checksum_type'] == 'md5':
                checksum = md5(rpm.metadata['filename'])

            if checksum == rpm.metadata['checksum']:
                print('local file matches: ' + rpm.metadata['filename'])
            else:
                print('local file MISMATCH: ' + rpm.metadata['filename'])
        else:
            rpm.retrieve()

    print json.dumps(results, indent=4)
