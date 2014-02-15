Juju Digital Ocean Provider
---------------------------

This package provides a cli plugin for juju that allows for cli based
provisioning of machines on digital ocean. I like to call it JuDo :-)

Digital ocean is linux vps provider utilizing kvm and ssd across
multiple data centers at a very competitive price with hourly billing.

Juju provides for workloads management and orchestration using a
collection of workloads definitions (charms) that can be assembled
lego fashion at runtime into complex application topologies.

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
must be uploaded to the digital ocean control panel. If you have
multiple keys there you can specify the key name to use when creating
instances via the environment variable DO_SSH_KEY, config file, or cli
parameter.

**Note** If you have a large number of ssh keys, ssh will only attempt
a certain number of key logins before giving up, ideally you want to
use one the keys it will select first. Its not possible at this moment
to specify a private key to use for ssh. (see http://pad.lv/1270466)

Juju Config
+++++++++++

Next let's configure a juju environment for digital ocean, add an
a null provider enviroment to 'environments.yaml', for example::

 environments:
   digitalocean:
      type: manual
      bootstrap-host: null
      bootstrap-user: root

Usage
=====

Now we can bootstrap an environment::

  $ juju docean bootstrap --constraints="mem=2g, region=nyc" --upload-tools

The --upload-tools parameter is required atm due to a juju bug 
http://pad.lv/1280678

All machines created by this plugin will have the juju environment
name as a prefix for their droplet name.

After our environment is bootstrapped we can add additional machines
to it via the the add-machine command, for example the following will
add 5 machines with 2Gb each::

  $ juju docean add-machine -n 5 --constraints="mem=2G"

We can now use standard juju commands for deploying workloads::

  $ juju deploy wordpress
  $ juju deploy mysql
  $ juju add-relation wordpress mysql
  $ juju status

We can terminate allocated machines by their machine id. By default
machines are forcibly terminated, which will also terminate any
units on those machines, and is not dependent on the machine actually
running.::

  $ juju docean terminate-machine 1 2 3

And we can destroy the entire environment via::

  $ juju docean destroy-environment


All commands have builtin help facilities and accept a -v option which will
print verbose output while running.

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

  - 'region' to denote the data center to utilize (currently 'ams2',
    'nyc1', 'nyc2', 'sfo1', 'sg1') defaulting to 'nyc2'.

  - 'transfer' to denote the terabytes of transfer included in the
    instance montly cost (integer size in gigabytes).


.. _here: https://www.digitalocean.com/?refcode=5df4b80c84c8
.. _juju constraints: https://juju.ubuntu.com/docs/reference-constraints.html
