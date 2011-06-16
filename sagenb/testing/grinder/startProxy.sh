#!/bin/bash
. setGrinderEnv.sh
java -cp $CLASSPATH net.grinder.TCPProxy -console -http > grinder.py
