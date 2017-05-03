#!/bin/bash

#bak the error log
cp /usr/local/nginx/logs/error.log /usr/local/nginx/logs/error/error-$(date -d "yesterday" +"%Y%m%d").log

#clean error log
cat /dev/null > /usr/local/nginx/logs/error.log

#copy the normal logs
cp /usr/local/nginx/logs/access.log /usr/local/nginx/logs/access/access-$(date -d "yesterday" +"%Y%m%d").log

#clean the normal logs
cat /dev/null > /usr/local/nginx/logs/access.log

