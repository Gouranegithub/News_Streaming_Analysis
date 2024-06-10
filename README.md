# launching The Application 

# Command uses

### Navigate to the location of your docker compose file
```cd .../SPARK STREAMING PFA```
### Install spark-master and spark-worker by executing the docker-compse.yml file
```docker compose -f docker-compose.yml up -d```
### Move into Kafka container
```docker exec -it kafkaa /bin/sh```
### Create Kafka topics
```kafka-topics.sh --create --zookeeper zookeeperr:2181 --replication-factor 1 --partitions 1 --topic Captions```
```kafka-topics.sh --create --zookeeper zookeeperr:2181 --replication-factor 1 --partitions 1 --topic Chats```
```kafka-topics.sh --create --zookeeper zookeeperr:2181 --replication-factor 1 --partitions 1 --topic Output```
### Move into spark-master container
```docker exec -it spark-master /bin/sh```
### submit the spark application
```spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.3 ./apps/app.py```
###  You can check the Spark web UI  at
```http://localhost:4040/```
### Navigate to the location of your flask appl file
```cd .../SPARK STREAMING PFA/flask_apps/web```
### Start the flask app
```python app.py```
###  You can check the interface at
```http://127.0.0.1:5000/```