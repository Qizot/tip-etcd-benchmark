package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

type BenchParamsLister interface {
    ToList() []string
}

type BenchParams struct {
	// list of coma separated endpoints pointing to etcd instances
	Endpoints string
	// number of clients that should be used for the benchmark
	Clients int
	// total number of put/range test cases
	Total int
	// number of connections
	Conns int
}

func (params BenchParams) ToList() []string {
	return []string{
		"--endpoints", params.Endpoints,
		"--clients", fmt.Sprintf("%d", params.Clients),
		"--total", fmt.Sprintf("%d", params.Total),
		"--conns", fmt.Sprintf("%d", params.Conns),
	}
}

type ReadBenchParams struct {
	BenchParams
	
	Key string
	EndRange string
	Consistency string
}

func (params ReadBenchParams) ToList() []string {
	baseParams := params.BenchParams.ToList()
	result := append([]string{"range", params.Key, params.EndRange, "--consistency", params.Consistency}, baseParams...)
	
	return result
}

type WriteBenchParams struct {
	BenchParams
	
	KeySize int
	ValSize int

	TargetLeader bool
	SequentialKeys bool
}

func (params WriteBenchParams) ToList() []string {
	baseParams := params.BenchParams.ToList()
	result := append([]string{
		"--key-size", fmt.Sprintf("%d", params.KeySize),
		"--val-size", fmt.Sprintf("%d", params.ValSize),
	}, baseParams...)

	if params.TargetLeader {
		result = append([]string{
			"--target-leader",
		}, result...)
	}

	if params.SequentialKeys {
		result = append([]string{
			"--sequential-keys",
		}, result...)
	}
	
	return result
}

func benchParamsFromRequest[Params any](req *http.Request) (Params, error) {
	var params Params

	// Try to decode the request body into the struct. If there is an error,
	// respond to the client with the error message and a 400 status code.
	err := json.NewDecoder(req.Body).Decode(&params)
	if err != nil {
		return params, err
	}

	return params, nil
}

func runBenchmark[Params BenchParamsLister](arguments []string, params Params) (string, error) {
	arguments = append(arguments, params.ToList()...)
	// arguments = append(
	// 	arguments,
	// 	"--endpoints", params.Endpoints,
	// 	"--clients", fmt.Sprintf("%d", params.Clients),
	// 	"--total", fmt.Sprintf("%d", params.Total),
	// )

	program := os.Getenv("BENCHMARK_EXEC")
	command := exec.Command(program, arguments...)

	log.Printf("Running benchmark command: %s\n", strings.Join(command.Args, " "))

	output, err := command.Output()
	if err != nil {
		error := fmt.Errorf("Failed to run benchmark command %+v\n", err)

		return "", error
	}

	return string(output), nil
}

func writeError(w http.ResponseWriter, err error) {
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusInternalServerError)
	w.Write([]byte(err.Error()))
}

func readBenchmark(w http.ResponseWriter, req *http.Request) {

	params, err := benchParamsFromRequest[ReadBenchParams](req)
	if err != nil {
		writeError(w, err)
		return
	}

	result, err := runBenchmark([]string{}, params)

	if err != nil {
		writeError(w, err)
		return
	}

	w.WriteHeader(200)
	fmt.Fprintf(w, "Result: %s\n", result)
}

func writeBenchmark(w http.ResponseWriter, req *http.Request) {
	params, err := benchParamsFromRequest[WriteBenchParams](req)
	if err != nil {
		writeError(w, err)
		return
	}

	result, err := runBenchmark([]string{"put"}, params)

	if err != nil {
		writeError(w, err)
		return
	}

	w.WriteHeader(200)
	fmt.Fprint(w, result)
}

func main() {
	http.HandleFunc("/benchmark/read", readBenchmark)
	http.HandleFunc("/benchmark/write", writeBenchmark)

	log.Println("Listening for benchmark requests...")
	http.ListenAndServe(":8080", nil)
}
