#!/usr/bin/python
from datetime import datetime
import time
import xmlrpclib

SATELLITE_URL = "http://spacewalk/rpc/api"
SATELLITE_LOGIN = "admin"
SATELLITE_PASSWORD = "password"

client = xmlrpclib.Server(SATELLITE_URL, verbose=0)

key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)
channel_list = client.channel.listSoftwareChannels(key)
print(channel_list)

package_list = client.channel.software.listAllPackages(key, channel_list[0]['label'])
print(package_list)

