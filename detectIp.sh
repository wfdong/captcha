#!/bin/bash
IP=`ping -c1 yanzhengma.f3322.net|awk -F'[(|)]' 'NR==1{print $2}'`
echo $IP
OLDIP=`tail /usr/local/nginx/changedips.log -n -1`
echo $OLDIP
if [ $IP = $OLDIP ]; then
echo eq
else
echo not eq
echo $IP >> /usr/local/nginx/changedips.log
`/usr/local/nginx/sbin/nginx -s reload`
fi
