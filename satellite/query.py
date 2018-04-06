#!/usr/bin/env python

import argparse
import xmlrpclib
import sys
import os
import requests
import hashlib


def argumentparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--server", type=str, help="satellite server hostname or ip address", required=True)
    parser.add_argument("-u", "--user", type=str, help="satellite username credential", required=True)
    parser.add_argument("-p", "--password", type=str, help="satellite password credential", required=True)
    parser.add_argument("-c", "--channel", type=str, help="satellite channel", required=True)
    args = parser.parse_args()
    return vars(args)


def sha256(fname):
    hash_md5 = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class Query:
    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.password = password
        self.api = 'http://' + server + '/rpc/api'
        self.client = xmlrpclib.Server(self.api, verbose=0)
        self.key = False

    def login(self):
        self.key = self.client.auth.login(self.user, self.password)

    def logout(self):
        self.client.auth.logout(self.key)
        self.key = False

    def get_channel_list(self):
        channel_list = self.client.channel.listSoftwareChannels(self.key)
        return channel_list

    def get_channel_package_list(self, channel_label):
        channel_package_list = self.client.channel.software.listAllPackages(self.key, channel_label)
        return channel_package_list

    def get_package_url(self, package_id):
        package_url = self.client.packages.getPackageUrl(self.key, package_id)
        return package_url


if __name__ == "__main__":
    args = argumentparser()
    q = Query(server=args['server'], user=args['user'], password=args['password'])

    q.login()
    channel_list = q.get_channel_list()

    channel_label = False
    for channel in channel_list:
        if channel['name'] == args['channel']:
            channel_label = channel['label']
            break

    if not channel_label:
        print "channel {0} not found".format(args['channel'])
        sys.exit(1)

    channel_package_list = q.get_channel_package_list(channel_label)

    url_list = []
    for package in channel_package_list:
        package_id = int(package['id'])
        package_url = q.get_package_url(package_id)
        url_list.append({'package_url': package_url, 'checksum': package['checksum']})

    for url in url_list:
        filename = os.path.basename(url['package_url'])

        if os.path.exists(filename):
            local_checksum = sha256(filename)
            if local_checksum != url['checksum']:
                print "local file MISMATCH: {0}".format(filename)
            else:
                print "local file matches: {0}".format(filename)
        else:
            print "retrieving {0}".format(filename)
            r = requests.get(url['package_url'])
            open(filename, 'wb').write(r.content)

    q.logout()
