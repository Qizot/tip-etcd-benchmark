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
    "total": 1000, // the number of total requests that should be performed against the database, either read or write
    "conns": 100 // number of concurrent connections
}
```

`read` benchmark specific parameters:
```json
{
    "key": "key to query",
    "endRange": "the range's end key when testing range performance",
    "consistency": "consistencty type of read query (l - Linearizable or s - Serializable)"
}
```

`write` benchmark specific parameters:
```json
{
    "keySize": "size of the key in bytes",
    "valSize": "size of the value in bytes",
    "sequentialKeys": "should the keys be sequential",
    "targetLeader": "should it query only the leader instance"
}
```

There are 2 endpoints available:
- `/benchmark/read` - tests the read performance (operation `range`)
- `/benchmark/write` - tests the write performance (operation `put`)
    
Example call with `curl`:

```bash
# watchout when using docker-compose setup as the localhost domain will map to `etcd`
# read benchmark
curl -d '{"endpoints": "10.0.0.251:2379", "clients": 5, "conns": 5, "total": 1000, "key": "foo", "endRange": "foo3", "consistency": "l"}'  http://localhost:8080/benchmark/read
# write benchmark
curl -d '{"endpoints": "10.0.0.251:2379", "clients": 5, "conns": 5, "total": 1000, "keySize": 4, "valSize": 64, "targetLeader": true, "sequentialKeys": true}'  http://localhost:8080/benchmark/read
```


## Containernet setup

1. Install containernet https://github.com/containernet/containernet#option-1-bare-metal-installation
2. Run the following command
```
cd containernet
sudo python3 setup.py install
```

3. Build docker images

```sh
./build.sh
```

4. Run etcd and benchamrk in containernet.

```sh
sudo python3 containernet-environment/main.py -c [ config_file_path ]
```  

Containernet `main.py` file accepts configuration files in a .json format. Example file:

```json
[
  {
    "ip": "10.0.0.251", // instance ip
    "mem": "100m", // memory limits
    "cpus": "8", // cpu limits in cpu units
    "bandwidth": 1000, // bandwith limits
    "link_delay": "3ms" 
  },
  {
    "ip": "10.0.0.252",
    "mem": "100m",
    "cpus": "8",
    "bandwidth": 1000,
    "link_delay": "3ms"
  }
]
```


5. Check cluster state:

```
etcd1 etcdctl member list
```

6. Then you can test it using:
```sh
curl -d '{"endpoints": "10.0.0.251:2379", "clients": 5, "conns": 5, "total": 1000, "key": "foo", "endRange": "foo3", "consistency": "l"}'  http://localhost:8080/benchmark/read
```


## Benchmarking etcd

Project includes benchmarking script. You can run it with:

```sh
sudo ./test.sh [ config_file_path ] [ result_file_name ]
``` 

Script is going to build docker images at first. Then it is going to set up Containernet environment and run benchmark using a set of scenarios.

Scenarios consist of a series of key writes followed by a series of reads. Write scenarios include single and multiclient writes with multiple connections openned for between 1000 and 100000 keys. What is more they cover also cluster and leader only writes. Read scenarios test etcd performance based on the consistency of operation, meaning that some of them require whole quorum to agree while the rest don't.

Benchmark results are saved to csv file under the name that is passed in one of the arguments. CSV contain columns that describe both benchmark results and scenario settings:

TestType  |  ClusterSize  |  RequestCount  |  ClientCount  |  ConnectionCount  |  KeySize  |  ValueSize  |  Consistency  |  Total     |  Slowest  |  Fastest  |  Average  |  Stddev  |  Requests/sec  |  10%     |  25%     |  50%     |  75%     |  90%     |  95%
----------|---------------|----------------|---------------|-------------------|-----------|-------------|---------------|------------|-----------|-----------|-----------|----------|----------------|----------|----------|----------|----------|----------|--------
write     |  2            |  100000        |  1000         |  100              |  4        |  64         |  -            |  144.9626  |  5.6176   |  0.6311   |  1.4391   |  0.2509  |  689.8333      |  1.3289  |  1.3804  |  1.4166  |  1.4381  |  1.4567  |  1.4728
write     |  2            |  100000        |  1000         |  100              |  8        |  256        |  -            |  302.7955  |  15.0167  |  0.6634   |  3.0120   |  0.8257  |  330.2559      |  2.6280  |  2.7675  |  2.8599  |  2.9412  |  2.9901  |  5.3955
read      |  2            |  100000        |  100          |  100              |  -        |  -          |  l            |  276.3772  |  0.9761   |  0.2372   |  0.2762   |  0.0219  |  361.8243      |  0.2586  |  0.2657  |  0.2759  |  0.2842  |  0.2918  |  0.2976
read      |  2            |  100000        |  100          |  100              |  -        |  -          |  s            |  264.3478  |  0.9440   |  0.2220   |  0.2642   |  0.0189  |  378.2895      |  0.2557  |  0.2584  |  0.2626  |  0.2682  |  0.2736  |  0.2769

 After the benchmark executes, the Containernet is shut down and topology is deleted.