package main

import (
	"encoding/json"
	"time"
)

type User struct {
	ID      int               `json:"id"`
	Name    string            `json:"name"`
	Email   string            `json:"email,omitempty"`
	Score   float64           `json:"score"`
	Active  bool              `json:"active"`
	Tags    []string          `json:"tags"`
	Meta    map[string]any    `json:"meta"`
	Created time.Time         `json:"created"`
	Parent  *User             `json:"parent,omitempty"`
	Raw     json.RawMessage   `json:"raw"`
	Attrs   map[string]string `json:"attrs"`
}
type Event struct {
	Kind  string    `json:"kind"`
	Count int64     `json:"count"`
	Ratio float32   `json:"ratio"`
	Level uint8     `json:"level"`
	Items []Item    `json:"items"`
	At    time.Time `json:"at"`
	Extra any       `json:"extra"`
}
type Item struct {
	SKU   string  `json:"sku"`
	Price float64 `json:"price"`
	Qty   int     `json:"qty"`
}
type Config struct {
	Name    string         `json:"name"`
	Port    int            `json:"port,string"`
	Debug   bool           `json:"debug"`
	Limits  map[string]int `json:"limits"`
	Servers []string       `json:"servers"`
	Num     json.Number    `json:"num"`
}

var factories = []func() any{
	func() any { return new(User) },
	func() any { return new(Event) },
	func() any { return new(Config) },
	func() any { return new(map[string]any) },
	func() any { return new([]any) },
	func() any { return new(map[string]string) },
	func() any { return new([]int) },
	func() any { return new(Item) },
}
var _ = json.Marshal
