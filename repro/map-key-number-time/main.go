package main

import (
	"encoding/json"
	"fmt"
	"time"
)

// Case 1: map key type with UnmarshalJSON (and no UnmarshalText of its own).
type Day struct{ time.Time }

func (d *Day) UnmarshalJSON(b []byte) error {
	t, err := time.Parse(`"2006-01-02"`, string(b))
	d.Time = t
	return err
}

// Case 1b: key type with both UnmarshalJSON and UnmarshalText.
type K struct{ S string }

func (k *K) UnmarshalJSON(b []byte) error { k.S = "json:" + string(b); return nil }
func (k *K) UnmarshalText(b []byte) error { k.S = "text:" + string(b); return nil }

func main() {
	var m1 map[Day]bool
	err := json.Unmarshal([]byte(`{"2018-12-12": true}`), &m1)
	fmt.Printf("1  map[Day]bool: %v err=%v\n", m1, err)

	var m2 map[K]int
	err = json.Unmarshal([]byte(`{"q": 1}`), &m2)
	fmt.Printf("1b map[K]int: %v err=%v\n", m2, err)

	var n struct {
		F json.Number `json:",string"`
	}
	err = json.Unmarshal([]byte(`{"F":"\"12\""}`), &n)
	fmt.Printf("2  json.Number ,string: %q err=%v\n", n.F, err)

	t := struct{ T time.Time }{time.Date(2016, 2, 2, 21, 0, 0, 0, time.UTC)}
	err = json.Unmarshal([]byte(`{"T":"2020-01-02"}`), &t)
	fmt.Printf("3  time.Time after failed parse: %v err=%v\n", t.T, err != nil)
}
