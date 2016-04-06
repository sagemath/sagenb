#!/usr/bin/env bash

# This script creates a new tarball for SageNB.
rm -rf dist

exec ./setup.py sdist --format=bztar
