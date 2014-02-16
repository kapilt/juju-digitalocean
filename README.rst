Juju Digital Ocean Provider
---------------------------

This package provides a cli plugin for juju that allows for cli based
provisioning of machines on digital ocean. I like to call it JuDo :-)

Digital ocean is linux vps provider utilizing kvm and ssd across
multiple data centers at a very competitive price with hourly billing.

Juju provides for workloads management and orchestration using a
collection of workloads definitions (charms) that can be assembled
lego fashion at runtime into complex application topologies.

http://juju.ubuntu.com

http://digitalocean.com


Install
=======

**This plugin requires a development version of juju (>= 1.17.2)**

A usable dev version of juju is available via the dev ppa::

  $ sudo add-apt-repository ppa:juju/devel
  $ apt-get update && apt-get install juju
  $ juju version
  1.17.2-saucy-amd64

Plugin installation is done via pip/easy_install which is the python language
package managers, its available by default on ubuntu. Also recommended
is virtualenv to sandbox this install from your system packages::

  $ pip install -U juju-docean

Fwiw, currently the transitive dependency tree is PyYAML, requests, dop.


Setup
=====

There are three steps for configuration and setup of this
provider. Configuring your digital ocean api keys, adding an
environment to juju's config file, and setting up an ssh key for usage
on digital ocean machines.

DO API Keys
+++++++++++

A digital ocean account is a pre-requisite, If you don't have a
digital ocean account you can sign up `here`_.

Credentials for the digital ocean api can be obtained from your account
dashboard at https://cloud.digitalocean.com/api_access

The credentials can be provided to the plugin via.

  - Environment variables DO_CLIENT_ID and DO_API_KEY

This digital ocean plugin uses the manual provisioning capabilities of
juju core. As a result its required to allocate machines in the
environment before deploying workloads. We'll explore that more in a
moment.

SSH Key
+++++++

An ssh key is required for use by this plugin and the public key
must be uploaded to the digital ocean control panel.

**Note** If you have a large number of ssh keys, ssh will only attempt
a certain number of key logins before giving up, ideally you want to
use one the keys it will select first. Its not possible at this moment
to specify a private key to use for ssh. (see http://pad.lv/1270466)

Juju Config
+++++++++++

Next let's configure a juju environment for digital ocean, add an
a null provider environment to 'environments.yaml', for example::

 environments:
   digitalocean:
      type: manual
      bootstrap-host: null
      bootstrap-user: root

Usage
=====

We need to tell juju which environment we want to use, there are
several ways to do this, either of the following will do the trick::

  $ juju switch digitalocean
  $ export JUJU_ENV=digitalocean

Now we can bootstrap our digital ocean environment::

  $ juju docean bootstrap --constraints="mem=2g, region=nyc1"

Which will create a droplet with 2Gb of ram in the nyc1 data center.

All machines created by this plugin will have the juju environment
name as a prefix for their droplet name if your looking at the DO
control panel.

After our environment is bootstrapped we can add additional machines
to it via the the add-machine command, for example the following will
add 3 machines with 2Gb each::

  $ juju docean add-machine -n 2 --constraints="mem=2G, region=nyc2"
  $ juju status

  environment: docean
  machines:
    "0":
      agent-state: started
      agent-version: 1.17.2.1
      dns-name: 162.243.115.78
      instance-id: 'manual:'
      series: precise
      hardware: arch=amd64 cpu-cores=1 mem=2002M
    "1":
      agent-state: started
      agent-version: 1.17.2.1
      dns-name: 162.243.86.238
      instance-id: manual:162.243.86.238
      series: precise
      hardware: arch=amd64 cpu-cores=1 mem=2002M
    "2":
      agent-state: started
      agent-version: 1.17.2.1
      dns-name: 107.170.39.10
      instance-id: manual:107.170.39.10
      series: precise
      hardware: arch=amd64 cpu-cores=1 mem=2002M
  services: {}

We can now use standard juju commands for deploying service workloads aka
charms::

  $ juju deploy wordpress

Without specifying the machine to place the workload on, the machine
will automatically go to an unused machine within the environment.

There are hundreds of available charms ready to be used, you can
find out more about what's out there from http://jujucharms.com
Or alternatively the 'plain' html version at
http://manage.jujucharms.com/charms/precise

We can use manual placement to deploy target particular machines::

  $ juju deploy mysql --to=2

And of course the real magic of juju comes in its ability to assemble
these workloads together via relations like lego blocks::

  $ juju add-relation wordpress mysql

We can terminate allocated machines by their machine id. By default with the
docean plugin, machines are forcibly terminated which will also terminate any
service units on those machines::

  $ juju docean terminate-machine 1 2

And we can destroy the entire environment via::

  $ juju docean destroy-environment

All commands have builtin help facilities and accept a -v option which will
print verbose output while running.

You can find out more about using from http://juju.ubuntu.com/docs

Constraints
===========

Constraints are selection criteria used to determine what type of
machine to allocate for an environment. Those criteria can be related
to size of the machine, its location, or other provider specific
criteria.

This plugin accepts the standard `juju constraints`_

  - cpu-cores
  - memory
  - root-disk

Additionally it supports the following provider specific constraints.

  - 'region' to denote the digital ocean data center to utilize. All digitalocean
    data centers are supported and various short hand aliases are defined. ie. valid
    values include ams2, nyc1, nyc2, sfo1, sg1. The plugin defaults to nyc2.

  - 'transfer' to denote the terabytes of transfer included in the
    instance montly cost (integer size in gigabytes).


.. _here: https://www.digitalocean.com/?refcode=5df4b80c84c8
.. _juju constraints: https://juju.ubuntu.com/docs/reference-constraints.html
