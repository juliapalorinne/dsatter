# DSatter
DSatter is a real-time chat service that is implemented as a Distributed System with the backend running on the edge of the cloud.


This project originally started as a course project for the course [Distributed Systems](https://studies.helsinki.fi/courses/cur/hy-opt-cur-2223-b8ec1422-835b-4bdb-bd2c-25df506de0f8/CSM13001/Distributed_Systems_Lectures), organized by the University of Helsinki.

The core system consists of two different types of nodes: one discovery node whose main task is to implement the naming service functionality, and a set of server nodes.


## Project (repo) structure

### Common
Contains common modules and types that are used by all types of nodes.

### Node client
Client application for the chat service. Serves as the users interface to the chat service.

### Node discovery
Serves node-servers and clients. Provides a REST endpoint for the different nodes. Assigns ids for node-servers and provides endpoints for them to register to or query statuses of their peers. Also provides a REST endpoint for clients to query for endpoints to connect to.

### Node server
Provides an endpoint for clients to connect to. Handles incoming messages, conveys them to other node-servers, and assures that all clients get all messages. The whole distributed system is designed so that a node-server can run in isolation by itself or as a part of a distributed system with *n* nodes. 

### Test perf
A simple test to test the performance of the system.

## Usage
The node discovery and server are packaged as npm packages and are implemented using Javascript running on nodejs. The client and performance test are packaged as python virtual environments. Instructions for running the python packages are given in their own README's.

## Running the distributed chat service backend
All nodes have 2 different environments configured; production and development. When running in the development environment additional checks and debug-prints are done. Also the startup differs a bit between the different modes. Detailed info about required arguments are given separately for each node in their own directories.

### Dockerized (production environment)
You can run the backend in production mode, utilizing the docker scripts. The provided scripts handle all required arguments.

#### Setting up Dockerized environment:
```
./build-images.sh
./start-containers.sh
```
#### Tearing down the Dockerized environment:
```
./teardown.sh
```

If you wish to only stop running the containers or delete the images or volumes, the following commands accomplish those respective actions:
```
./stop-containers.sh
./delete-images.sh
./delete-volumes.sh
```

### Localhost (development environment)
You can run the project on localhost by following the detailed instructions for each node in their README's. Start by setting up the environments for each node. When the environments are set up run one instance of the node-discovery. After that you can continue by running n instances node-servers. When running the node-servers in dev-env on localhost, there is a small chance for port colliding, since the listening ports are selected randomly from a set of 1000 ports. This is not handled in any way. In case of any errors, delete all *.db -files from both the discovery and the server nodes' directories before restarting the system. Most errors happen when the node-servers are terminated forcefully and are not given a chance to unregister themself from the discovery node.
