import sys
import requests
import json
import argparse
from subprocess import Popen, PIPE
import signal

BENCHMARK_COLUMNS = ["Total", "Slowest", "Fastest",
  "Average", "Stddev", "Requests/sec", "10%", "25%",
  "50%", "75%", "90%", "95%"] 

CONFIG_COLUMNS = ["TestType", "ClusterSize", "RequestCount", 
  "ClientCount", "ConnectionCount", "KeySize", "ValueSize", "Consistency", "TargetLeader"]

CSV_FIELDS = [*CONFIG_COLUMNS, *BENCHMARK_COLUMNS] 

CLUSTER_TEST_SCENARIOS = {
  'write':[
    { "conns": 1, "clients": 1, "total": 1000, "keySize": 4, "valSize": 64, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 1, "clients": 1, "total": 1000, "keySize": 8, "valSize": 256, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 4, "valSize": 64, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 8, "valSize": 256, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 4, "valSize": 64, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 8, "valSize": 256, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 4, "valSize": 64, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 8, "valSize": 256, 'targetLeader': True, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 4, "valSize": 64, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 8, "valSize": 256, 'sequentialKeys': True },
  ],
  'read':[
    { "conns": 1, "clients": 1, "total": 1000, 'consistency':'l' },
    { "conns": 1, "clients": 1, "total": 1000, 'consistency':'s' },
    { "conns": 100, "clients": 100, "total": 10000, 'consistency':'l' },
    { "conns": 100, "clients": 100, "total": 10000, 'consistency':'s' },
    { "conns": 100, "clients": 100, "total": 100000, 'consistency':'l' },
    { "conns": 100, "clients": 100, "total": 100000, 'consistency':'s' },
  ],
}

STANDALONE_TEST_SCENARIOS = {
  'write':[
    { "conns": 1, "clients": 1, "total": 1000, "keySize": 4, "valSize": 64, 'sequentialKeys': True },
    { "conns": 1, "clients": 1, "total": 1000, "keySize": 8, "valSize": 256,  'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 4, "valSize": 64, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 10000, "keySize": 8, "valSize": 256, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 4, "valSize": 64, 'sequentialKeys': True },
    { "conns": 100, "clients": 1000, "total": 100000, "keySize": 8, "valSize": 256, 'sequentialKeys': True },
  ],
  'read':[
    { "conns": 1, "clients": 1, "total": 1000, 'consistency':'l' },
    { "conns": 1, "clients": 1, "total": 1000, 'consistency':'s' },
    { "conns": 100, "clients": 100, "total": 10000, 'consistency':'l' },
    { "conns": 100, "clients": 100, "total": 10000, 'consistency':'s' },
    { "conns": 100, "clients": 100, "total": 100000, 'consistency':'l' },
    { "conns": 100, "clients": 100, "total": 100000, 'consistency':'s' },
  ],
}

def timeout_handler(signum, frame):   # Custom signal handler
  print('TIMEOUT')
  exit(1)

def map_scenario_to_csv(scenario):
  return [str(scenario['total']), str(scenario['clients']), 
    str(scenario['conns']), str(scenario.get('keySize', '-')),
    str(scenario.get('valSize', '-')), str(scenario.get('consistency', '-')), str(scenario.get('targetLeader', '-'))]

def read_config_file_contents(file_path):

  configs = json.load(open(config_file_path))

  if type(configs) != list or len(configs) < 1:
      raise RuntimeError("The config file should be a json array containing at least one instance")

  return configs

def run_tests(file_path, output_file, benchmark_address):
  configs = read_config_file_contents(file_path)
  endpoints = [f'{member["ip"] + ":2379"}' for member in configs]

  output_file.write(','.join(CSV_FIELDS) + '\n')

  is_cluster = len(configs) > 1
  scenario_group = CLUSTER_TEST_SCENARIOS if is_cluster else STANDALONE_TEST_SCENARIOS

  payload = { **scenario_group['write'][0], "endpoints": ','.join(endpoints)} # dummy request to make sure that etcd is already up
  output_text = requests.post(benchmark_address + '/write',  data=json.dumps(payload)).text

  def parse_output(output_text):
    parsed_output = {}
    
    for line in output_text.split('\n'):
      line_items = line.split()
      if len(line_items) >= 2 and line_items[0].strip(':') in BENCHMARK_COLUMNS:
        column = line_items[0].strip(':')
        value = line_items[1] if not line_items[1].islower() else line_items[2] 
        parsed_output[column] = value
    
    sorted_output = [parsed_output.get(x, '-') for x in BENCHMARK_COLUMNS]
    return sorted_output 

  for benchmark_type in ['write', 'read']:
    for scenario in scenario_group[benchmark_type]:
      print(f'Testing {benchmark_type} scenario: {scenario["total"]} requests, {scenario["conns"]} connections, {scenario["clients"]} clients')
      additionalFields = {} if benchmark_type == 'write' else {'key': 'foo', 'endRange': 'foo3'}
      payload = { **scenario, "endpoints": ','.join(endpoints), **additionalFields}
      output_text = requests.post(benchmark_address + '/' + benchmark_type,  data=json.dumps(payload)).text
      parsed_output = parse_output(output_text)

      output_file.write(','.join([benchmark_type, str(len(configs)), *map_scenario_to_csv(scenario), *parsed_output])+ '\n')



signal.signal(signal.SIGALRM, timeout_handler)

args = sys.argv
config_file_path = args[1]
output_file_name = args[2]
benchmark_address = args[3]


proc = Popen(['python3', './containernet-environment/main.py', '-c', config_file_path], stdout=PIPE, stdin=PIPE)

signal.alarm(30)    

while True:
  line = proc.stdout.readline()
  x = line.decode()
  if x.strip() == "Ready":
    signal.alarm(0)
    break


output_file = open(output_file_name, "w")
print("Running Tests")
run_tests(config_file_path, output_file, benchmark_address)

    