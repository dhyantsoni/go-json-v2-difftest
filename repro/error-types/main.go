package main

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"time"
)

type S struct {
	B []byte
	T time.Time
	N int `json:",string"`
}

func main() {
	var s S
	err := json.Unmarshal([]byte(`{"B":"!!"}`), &s)
	var ce base64.CorruptInputError
	fmt.Printf("base64 bad:  %T  errors.As(CorruptInputError)=%v\n", err, errors.As(err, &ce))
	err = json.Unmarshal([]byte(`{"N":"x1"}`), &s)
	var ne *strconv.NumError
	fmt.Printf("string num:  %T  errors.As(*NumError)=%v\n", err, errors.As(err, &ne))
	err = json.Unmarshal([]byte(`{"T":"2020-01-02"}`), &s)
	var pe *time.ParseError
	fmt.Printf("time parse:  %T  errors.As(*time.ParseError)=%v\n", err, errors.As(err, &pe))
	// destination after failed time parse
	s2 := S{T: time.Date(2016, 2, 2, 21, 0, 0, 0, time.UTC)}
	err = json.Unmarshal([]byte(`{"T":"2020-01-02"}`), &s2)
	fmt.Printf("time keep:   err=%v  T after error=%v\n", err != nil, s2.T)
	// json.Number with ,string
	var n struct{ F json.Number `json:",string"` }
	err = json.Unmarshal([]byte(`{"F":"\"12\""}`), &n)
	fmt.Printf("Number str:  err=%T value=%q\n", err, n.F)
}
