#!/bin/bash

# Start the SSH service
service ssh start

# Check if Spark is being used as master or worker
if [ "$1" = "master" ]; then
    # Start the Spark master
    $SPARK_HOME/sbin/start-master.sh
elif [ "$1" = "worker" ]; then
    # Start the Spark worker
    $SPARK_HOME/sbin/start-slave.sh $SPARK_MASTER
else
    echo "Unknown role: $1. Use 'master' or 'worker'."
    exit 1
fi

# Keep the container running
tail -f /dev/null
