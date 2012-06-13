#!/usr/bin/env bash

# This script should be run when creating a new SPKG for shipping sagenb
# with Sage. For more complete instructions on how to generate a new
# SPKG, read the SPKG.txt file in the current SPKG.

die () {
    echo >&2 "$@"
    exit 1
}

cd ${0%/*}

git diff --quiet && git diff --cached --quiet ||
    die "Uncommitted changes in sagenb - please commit, stash, or discard"

rm -rf dist
mkdir -p dist

echo "Fetching source tarballs of (sub)dependencies of sagenb to dist/"
python util/fetch_deps.py dist || die "Couldn't fetch all (sub)dependencies"

echo "Creating source tarball of sagenb itself in dist/"
python setup.py sdist > sdist.log || die "Couldn't make sagenb source tarball"

echo "Sanitizing sagenb git repo (with backup)"
mv .git .git-backup
git init
git fetch .git-backup
git remote add sagemath https://github.com/sagemath/sagenb
git branch -f master FETCH_HEAD
git branch --set-upstream master sagemath/master
git reset --mixed
git gc --aggressive --prune=0

echo "Moving sanitized sagenb git repo to dist/"
mv .git dist/sagenb.git

echo "Restoring backup of git repo"
mv .git-backup .git

echo "Done!"
