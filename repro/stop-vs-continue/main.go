package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

type Bad struct{}

func (*Bad) UnmarshalJSON([]byte) error { return errors.New("bad") }

func main() {
	var a struct {
		T time.Time
		B string
	}
	err := json.Unmarshal([]byte(`{"T":"not a time","B":"after"}`), &a)
	fmt.Printf("time.Time error:      B=%q err=%v\n", a.B, err != nil)

	var b struct {
		P int `json:",string"`
		B string
	}
	err = json.Unmarshal([]byte(`{"P":"x1","B":"after"}`), &b)
	fmt.Printf(",string error:        B=%q err=%v\n", b.B, err != nil)

	var c struct {
		X Bad
		B string
	}
	err = json.Unmarshal([]byte(`{"X":1,"B":"after"}`), &c)
	fmt.Printf("UnmarshalJSON error:  B=%q err=%v\n", c.B, err != nil)

	var d struct {
		N int
		B string
	}
	err = json.Unmarshal([]byte(`{"N":"str","B":"after"}`), &d)
	fmt.Printf("type mismatch (ctrl): B=%q err=%v\n", d.B, err != nil)
}
