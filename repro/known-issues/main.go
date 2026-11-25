package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type SK string // string-kind key with MarshalText (#81355)

func (k SK) MarshalText() ([]byte, error) { return []byte("x" + string(k)), nil }

type Mi interface{ json.Marshaler } // interface embedding Marshaler (#82682)
type PM struct{}

func (*PM) MarshalJSON() ([]byte, error) { return []byte(`1`), nil }

type Fallback struct {
	Rest map[string]any `json:",embed"`
}
type inner struct{ *Fallback }

func show(name string, f func() string) {
	defer func() {
		if p := recover(); p != nil {
			fmt.Printf("%-7s PANIC %v\n", name, strings.SplitN(fmt.Sprint(p), "\n", 2)[0])
		}
	}()
	fmt.Printf("%-7s %s\n", name, f())
}

func main() {
	show("#81061", func() string {
		var v struct{ S string `json:",string"` }
		err := json.Unmarshal([]byte(`{"S":"null"}`), &v)
		return fmt.Sprintf("%q err=%v", v.S, err != nil)
	})
	show("#81062", func() string {
		var v struct{ F float32 }
		err := json.Unmarshal([]byte(`{"F":1e39}`), &v)
		return fmt.Sprintf("%v err=%v", v.F, err != nil)
	})
	show("#81355", func() string {
		b, err := json.Marshal(map[SK]int{"a": 1})
		return fmt.Sprintf("%s err=%v", b, err != nil)
	})
	show("#81373", func() string {
		var m map[float64]int
		err := json.Unmarshal([]byte(`{"1.5":1}`), &m)
		return fmt.Sprintf("%v err=%v", m, err != nil)
	})
	show("#81383", func() string {
		b, _ := json.Marshal(struct{ A int `json:"a!b"` }{1})
		return string(b)
	})
	show("#82682", func() string {
		b, err := json.Marshal(struct{ X Mi }{X: (*PM)(nil)})
		return fmt.Sprintf("%s err=%v", b, err != nil)
	})
	show("#82685", func() string {
		b, _ := json.Marshal("a\xffb")
		return string(b)
	})
	show("#82872", func() string {
		var m map[int]int
		err := json.Unmarshal([]byte(`{"null":1}`), &m)
		return fmt.Sprintf("%v err=%v", m, err != nil)
	})
	show("#81297", func() string {
		type outer struct {
			A int
			inner
		}
		var v outer
		err := json.Unmarshal([]byte(`{"A":1,"unmatched":2}`), &v)
		return fmt.Sprintf("A=%d err=%v", v.A, err != nil)
	})
}
