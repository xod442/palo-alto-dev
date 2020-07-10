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


HOSTNAME = "54.160.4.246"
USERNAME = "admin"
PASSWORD = "Grape123"
INTERFACE = "ethernet1/5"
IPADDRESS = ['1.1.1.1/23','2.2.2.2/23','3.3.3.3/23','4.4.4.4/24','5.5.5.5/24','6.6.6.6/24']


'''
Handling HA

# Don't assume either firewall is primary or active.
# Just start by telling pandevice they are an HA pair
# and how to connect to them.
fw = Firewall('10.0.0.1', 'admin', 'password')
fw.set_ha_peers(Firewall('10.0.0.2', 'admin', 'password'))

# Notice I didn't save the second firewall to a variable, because I don't need it.
# The point is to treat the HA pair as one firewall, so we only need one variable.
# This way, we have only one pandevice configuration tree to manage,
# NOT one tree for each fw in the pair.

# At this point, it's a good idea to collect the active/passive state from
# the live devices. This stores which firewall is active to an internal
# state machine in the Firewall object.
fw.refresh_ha_active()

# Now, verify the config is synced between the devices.
# If it's not synced, force config synchronization from active to standby
if not fw.config_synced():
    fw.synchronize_config()  # blocks until synced or error

'''


def main():
    # Before we begin, you'll need to use the pandevice documentation both
    # for this example and for any scripts you may write for yourself.  The
    # docs can be found here:
    #
    # http://pandevice.readthedocs.io/en/latest/reference.html
    #
    # First, let's create the firewall object that we want to modify.
    fw = firewall.Firewall(HOSTNAME, USERNAME, PASSWORD)
    print("Firewall system info: {0}".format(fw.refresh_system_info()))

    print("Desired interface: {0}".format(INTERFACE))

    # Set up some default variables
    zone = 'fake'
    router = 'default'
    comment = 'wookieware rocks'
    management_profile = None
    mtu = 1400

    # Sanity Check #1: the intent here is that the interface we
    # specified above should not already be in use.  If the interface is
    # already in use, then just quit out.
    print("List interfaces currently in use...")
    interfaces = network.EthernetInterface.refreshall(fw, add=False)
    for eth in interfaces:
        #if eth.name == INTERFACE:
        print("Interface {0}".format(eth))

    vsys_list = device.Vsys.refreshall(fw, name_only=True)
    print("Found the following vsys: {0}".format(vsys_list))

    # Choose one of the vsys at random to put it into.
    vsys = random.choice(vsys_list)


    # Let's make our base interface that we're going to make subinterfaces
    # out of.
    print("Creating base interface {0} in layer2 mode".format(INTERFACE))
    base = network.EthernetInterface(INTERFACE, "layer3")


    # Like normal, after creating the object, we need to add it to the
    # firewall, then finally invoke "create()" to create it.
    fw.add(base)
    base.create()


    # Now let's go ahead and make all of our subinterfaces.
    print 'Creating interfaces'
    eth = None
    array_counter = 0
    for tag in range(1, 7):
        ip = IPADDRESS[array_counter]
        name = "{0}.{1}".format(INTERFACE, tag)
        sub_intf = network.Layer3Subinterface(name,tag,ip,comment,management_profile,mtu)


        # Now add the subinterface to that randomly chosen vsys.
        vsys.add(sub_intf)
        vr = sub_intf.set_virtual_router(virtual_router_name=router)
        security_zone = sub_intf.set_zone(zone_name=zone)

        # security_zone = network.Interface.set_zone(eth,zone,refresh=True,update=True)
        #zone = network.Interface.set_zone(eth,zone_name=zone, mode='layer3')
        # vr = network.Interface.set_virtual_router(eth,router,refresh=True)
        # vr = network.Interface.set_virtual_router(interface=name,virtual_router_name=router)



        array_counter = array_counter + 1

    # You'll notice that we didn't invoke "create()" on the subinterfaces like
    # you would expect.  This is because we're going to use the bulk create
    # function to create all of the subinterfaces in one shot, which has huge
    # performance gains from doing "create()" on each subinterface one-by-one.
    #
    # The function we'll use is "create_similar()".  Create similar is saying,
    # "I want to create all objects similar to this one in my entire pandevice
    # object tree."  In this case, since we'd be invoking it on a subinterface
    # of INTERFACE (our variable above), we are asking pandevice to create all
    # subinterfaces of INTERFACE, no matter which vsys it exists in.
    #
    # We just need any subinterface to do this.  Since our last subinterface
    # was saved to the "eth" variable in the above loop, we can just use that
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
