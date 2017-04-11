package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

func benchMark(nums int, sigChan chan byte) {
	fmt.Println("benMark start")
	for i := 0; i < nums; i++ {
		resp, err := http.Get("http://0.0.0.0:5060/api/spamfilter?query=赚钱test宝妈tes日赚学生兼职*.@打字员")
		//	resp, err := http.Get("http://0.0.0.0:10001/health")
		if err != nil {
			// handle error
			fmt.Printf("get failed:%v\n", err)
			continue
		}

		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			// handle error
			fmt.Printf("read rsp failed:%v\n", err)
			continue
		}
		fmt.Printf("%v\n", string(body))
	}
	sigChan <- 1
}

func report(beg, end time.Time, num int) {
	delta := end.Sub(beg)
	fmt.Printf("%v requests finish in %d mspecs,qps = %v\n", num, delta/time.Millisecond,
		float64(num)/float64(float64(delta)/float64(time.Second)))
}

func main() {
	fmt.Println("vim-go")
	var size = flag.Int("c", 10, "cleints num ")
	var nums = flag.Int("n", 10000, "request num")
	flag.Parse()
	//resp, err := http.Get("http://www.01happy.com/demo/accept.php?id=1")
	/*
		resp, err := http.Get("http://0.0.0.0:5060/api/spamfilter?query=赚钱test宝妈tes日赚学生兼职*.@打字员")
		if err != nil {
			// handle error
			fmt.Printf("get failed:%v\n", err)
			return
		}

		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			// handle error
			fmt.Printf("read rsp failed:%v\n", err)
			return
		}
	*/
	//fmt.Println(string(body))
	sigChan := make(chan byte, *size)
	beg := time.Now()
	for i := 0; i < *size; i++ {
		go benchMark(*nums, sigChan)
	}
	for i := 0; i < *size; i++ {
		<-sigChan
	}
	end := time.Now()

	report(beg, end, (*size)*(*nums))
}
