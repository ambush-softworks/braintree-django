#!/bin/sh

python -m build
rm -f /tmp/braintree_django-*.tar.gz
cp ./dist/braintree_django-*.tar.gz /tmp/
rm ./dist/braintree_django-*.tar.gz