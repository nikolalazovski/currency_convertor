#!/bin/sh

while !</dev/tcp/db/5432; do
sleep 1;
done;

flask init-db

exec "$@"
