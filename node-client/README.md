# DSatter chat client node
A chat client for the distributed chat service

## Environment setup
Start by setting up the environment. Requires python3 version 3.8.10+.

```shell
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
...
deactivate (exit virtual environment)
```

## Running
After setting up the environment you can run the client without any arguments or by following the instructions:
```shell
./main.py -h

usage: main.py [-h] [-lv] [-d NODE_DISCOVERY_URL] [-s NODE_SERVER_URL]

Chat client for DSatter. If the client is run without the optional -s or -d
arguments, then it will attempt to query the discovery service for node-
servers using the same url as on the previous time it was run. Creates a
config.ini file, where it saves the settings. Delete this file to use default
values. This app has been developed and tested using python 3.8.10.

optional arguments:
  -h, --help            show this help message and exit
  -lv, --log-verbose    Enable verbose (debug) logging
  -d NODE_DISCOVERY_URL, --discovery NODE_DISCOVERY_URL
                        Url with port to a running node-discovery server to
                        use. Defaults to `http://localhost:8080/api/clients`
  -s NODE_SERVER_URL, --server NODE_SERVER_URL
                        Url with a port in case you want to connect to a
                        specific node-server. By default queries the discovery
                        service for active node-servers.
```

When the client is terminated it will save the settings in a file called `config.ini`, which is interpreted at startup. Default values are used if this file does not exist or any setting is missing from it.
