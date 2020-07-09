#!/usr/bin/env python

# Copyright (c) 2017, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# __author__ = "@netwookie"
# __credits__ = ["Rick Kauffman"]
# __license__ = "Apache2.0"
# __maintainer__ = "Rick Kauffman"
# __email__ = "rick.a.kauffman@hpe.com"

"""
bulk_subinterfaces.py
=====================

Use bulk operations to create / delete hundreds of firewall interfaces.

NOTE: Please update the hostname and auth credentials variables
      before running.

The purpose of this script is to use and explain both the bulk operations
as it relates to subinterfaces as well as the new function that organizes
objects into vsys.  This script will show how the new bulk operations
correctly handle when subinterface objects are in separate vsys trees.

"""

import datetime
import random
import sys

from pandevice import device
from pandevice import firewall
from pandevice import network


HOSTNAME = "10.10.10.1"
USERNAME = "admin"
PASSWORD = "password"
INTERFACE = "ethernet1/5"
# Creat list of IP's we will read from CSV file later.
IPADDRESS = ['1.1.1.1/23','2.2.2.2/23','3.3.3.3/23','4.4.4.4/24','5.5.5.5/24','6.6.6.6/24']


def main():
    # http://pandevice.readthedocs.io/en/latest/reference.html
    #
    # First, let's create the firewall object that we want to modify.
    fw = firewall.Firewall(HOSTNAME, USERNAME, PASSWORD)

    # Firewall has only one vsys.
    vsys_list = device.Vsys.refreshall(fw, name_only=True)
    vsys = random.choice(vsys_list)

    # Let's make our base interface that we're going to make subinterfaces
    # out of.
    base = network.EthernetInterface(INTERFACE, "layer3")

    # Like normal, after creating the object, we need to add it to the
    # firewall, then finally invoke "create()" to create it.
    fw.add(base)
    base.create()

    # Set up some default variables for the sub interfaces
    zone = 'local_vlans'
    router = 'default'
    comment = 'comment'
    management_profile = None
    mtu = 1400

    # Now let's go ahead and make all of our subinterfaces.
    eth = None
    array_counter = 0
    for tag in range(1, 7):
        ip = IPADDRESS[array_counter]
        name = "{0}.{1}".format(INTERFACE, tag)
        sub_intf = network.Layer3Subinterface(name,tag,ip,comment,management_profile,mtu)
        # Now add the subinterface.
        vsys.add(sub_intf)
        vr = sub_intf.set_virtual_router(virtual_router_name=router)
        security_zone = sub_intf.set_zone(zone_name=zone)
        array_counter = array_counter + 1

    # to invoke "create_similar()".
    print("Creating subinterfaces...")
    start = datetime.datetime.now()
    sub_intf.create_similar()
    vsys.add(vr)
    vsys.add(security_zone)
    vr.create()
    security_zone.create()
    print("Creating subinterfaces took: {0}".format(datetime.datetime.now() - start))



if __name__ == "__main__":
    # This script doesn't take command line arguments.  If any are passed in,
    # then print out the script's docstring and exit.
    if len(sys.argv) != 1:
        print(__doc__)
    else:
        # No CLI args, so run the main function.
        main()
