#!/bin/bash

# This script should be run when creating a new SPKG for shipping sagenb with
# Sage. For more complete instructions on how to generate a new SPKG, read the
# SPKG.txt file in the current SPKG.

die () {
    echo >&2 "$@"
    exit 1
}

cd ${0%/*}

rm -rf dist
mkdir -p dist

echo "Fetching source tarballs of (sub)dependencies of sagenb"
python fetch_deps.py dist || die "Couldn't fetch all (sub)dependencies"

echo "Creating source tarball of sagenb itself"
python setup.py sdist || die "Couldn't make sagenb source tarball"

echo "Done!"
