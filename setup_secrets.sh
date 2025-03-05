#!/bin/bash
set -eux

mkdir -p secrets/ssl
mkdir -p logs
mkdir -p site

function password() {
  head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12
}

## Setup flask secret key password
if [ ! -f secrets/flask-secret-key.txt ]; then
  echo Creating Flask secret key...
  password > secrets/flask-secret-key.txt
fi

## Setup elasticsearch password
if [ ! -f secrets/elastic-password.txt ]; then
  echo Creating elastic password...
  # password > secrets/elastic-password.txt
  echo -n elastic > secrets/elastic-password.txt
fi

## Setup admin password
if [ ! -f secrets/admin-password.txt ]; then
  echo Creating admin password...
  # password > secrets/elastic-password.txt
  password > secrets/admin-password.txt
fi

# elasticsearch refuses to start if permissions are not correct.
chmod 600 secrets/elastic-password.txt
# This is required because ES requires a specific owner and permissions
# that make the file unreadable to the host when running in github actions.
cp secrets/elastic-password.txt secrets/elastic-password.txt.orig

## Set up API key
# file has to exist for docker secret binding to work.
touch secrets/elastic-api-key.txt

## Set up SSL
SSL=secrets/ssl
if [ ! -f $SSL/beekey.buzz.private.key.pem ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $SSL/beekey.buzz.private.key.pem \
    -out $SSL/beekey.buzz.domain.cert.pem -subj \
    "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost" > /dev/null
fi
if [ ! -f $SSL/nytspellingbeesolver.com.key.pem ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $SSL/nytspellingbeesolver.com.key.pem \
    -out $SSL/nytspellingbeesolver.com.cert.pem -subj \
    "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost" > /dev/null
fi
