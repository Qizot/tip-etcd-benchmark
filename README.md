# ETCD benchmark using Containernet


## Structure

The project contains a bunch of folders:

- `benchmark-client` which is a `go` command line benchmark
- `benchmark-server` a simple `go` http server that is responsible for running the `benchmark-client` process under the hood
    and returns the results
- `containernet-environment` - the test containernet setup that should start the `etcd` database and `benchmark-server` with arbitrary
  network topology and resources limit
  
## Benchmark server
The benchmark server is responsible for receiving http requests with the following body payload:
```json
{
    "endpoints": "comma separated list of etcd instances with their respective ports e.g. localhost:2379,localhost:2380",
    "clients": 2, // a number of clients that should be used for performing a single benchmark,
    "total": 1000 // the number of total requests that should be performed against the database, either read or write
}
```

Additionally the `read` benchmark has the additional parameters:
```json
{
    "key": "key to query",
    "endRange": "the range's end key when testing range performance"
}
```

There are 2 endpoints available:
- `/benchmark/read` - tests the read performance (operation `range`)
- `/benchmark/write` - tests the write performance (operation `put`)
    
Example call with `curl`:

```bash
# watchout when using docker-compose setup as the localhost domain will map to `etcd`
# read benchmark
curl -d '{"endpoints": "localhost:2379", "clients": 5, "total": 1000, "key": "foo", "endRange": "foo3"}'  http://localhost:8080/benchmark/read
# write benchmark
curl -d '{"endpoints": "localhost:2379", "clients": 5, "total": 1000}'  http://localhost:8080/benchmark/write
```


## Containernet setup

1. Install containernet https://github.com/containernet/containernet#option-1-bare-metal-installation
2. Run the following command
```
cd containernet
sudo python3 setup.py install
```

```sh
./run.sh
```
    
Then you can test it using:
```sh
curl -d '{"endpoints": "10.0.0251:2379", "clients": 5, "total": 1000, "key": "foo", "endRange": "foo3"}'  http://localhost:8080/benchmark/read
```

To check cluster state run
```
etcd1 etcdctl member list
```
