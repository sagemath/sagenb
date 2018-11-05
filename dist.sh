#!/usr/bin/env bash

# This script creates a new tarball for SageNB

# Remove some auto-generated packaging directories
rm -rf dist sagenb.egg-info

# Ensure that we are packaging from a clean git repo
git clean -i -d -x

# Now actually create the package
exec ./setup.py sdist --format=bztar
