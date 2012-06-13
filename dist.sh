#!/usr/bin/env bash

# This script should be run when creating a new SPKG for shipping sagenb
# with Sage. For more complete instructions on how to generate a new
# SPKG, read the SPKG.txt file in the current SPKG.

die () {
    echo >&2 "$@"
    exit 1
}

cd ${0%/*}

rm -rf dist
mkdir -p dist

echo "Fetching source tarballs of (sub)dependencies of sagenb"
python util/fetch_deps.py dist || die "Couldn't fetch all (sub)dependencies"

echo "Sanitizing sagenb git repo (with backup)"
git diff --quiet ||
    die "Uncommitted changes in sagenb - please commit, stash, or discard"
mv .git .git-backup
git init
git fetch .git-backup
git branch -f master FETCH_HEAD
git gc --aggressive --prune=0

echo "Creating source tarball of sagenb itself"
python setup.py sdist || die "Couldn't make sagenb source tarball"

echo "Restoring backup of git repo"
rm -rf .git
mv .git-backup .git

echo "Done!"
