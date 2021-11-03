#!/bin/sh

# See http://download.bareos.org/bareos/release/
# for applicable releases and distributions

 DIST=CentOS_7

RELEASE=release/latest/
# RELEASE=experimental/nightly/

# add the Bareos repository
URL=http://download.bareos.org/bareos/$RELEASE/$DIST
wget -O /etc/yum.repos.d/bareos.repo $URL/bareos.repo

# install Bareos packages
yum install bareos bareos-database-postgresql
