package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type Plain string
type TU string

func (t *TU) UnmarshalText(b []byte) error { *t = TU(strings.ToUpper(string(b))); return nil }

func main() {
	var a struct{ F Plain `json:",string"` }
	err := json.Unmarshal([]byte(`{"F":"\"x\""}`), &a)
	fmt.Printf("named string, no methods:  %q err=%v\n", a.F, err)
	var b struct{ F TU `json:",string"` }
	err = json.Unmarshal([]byte(`{"F":"\"x\""}`), &b)
	fmt.Printf("named string + UnmarshalText: %q err=%v\n", b.F, err)
	var c struct{ F json.Number `json:",string"` }
	err = json.Unmarshal([]byte(`{"F":"\"12\""}`), &c)
	fmt.Printf("json.Number:               %q err=%v\n", c.F, err != nil)
	var d struct{ F string `json:",string"` }
	err = json.Unmarshal([]byte(`{"F":"\"x\""}`), &d)
	fmt.Printf("plain string (control):    %q err=%v\n", d.F, err)
}
