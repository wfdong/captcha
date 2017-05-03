#!/bin/sh
#del the logs 1 days ago
find /usr/local/nginx/logs/error -mtime +1 -type f -name \*.log | xargs rm -f

find /usr/local/nginx/logs/access -mtime +1 -type f -name \*.log | xargs rm -f

