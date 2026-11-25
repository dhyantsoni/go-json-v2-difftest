package main

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"time"
)

// dump renders a value deterministically without encoding/json.
func dump(v reflect.Value, depth int) string {
	if depth > 12 {
		return "..."
	}
	switch v.Kind() {
	case reflect.Invalid:
		return "<invalid>"
	case reflect.Pointer:
		if v.IsNil() {
			return "nil"
		}
		return "&" + dump(v.Elem(), depth+1)
	case reflect.Interface:
		if v.IsNil() {
			return "nil"
		}
		return fmt.Sprintf("(%s)%s", v.Elem().Type(), dump(v.Elem(), depth+1))
	case reflect.Struct:
		if v.Type().String() == "time.Time" {
			return fmt.Sprintf("time(%v)", v.Interface())
		}
		var b strings.Builder
		b.WriteString("{")
		for i := 0; i < v.NumField(); i++ {
			b.WriteString(v.Type().Field(i).Name + ":" + dump(v.Field(i), depth+1) + " ")
		}
		b.WriteString("}")
		return b.String()
	case reflect.Slice:
		if v.IsNil() {
			return "nilslice"
		}
		fallthrough
	case reflect.Array:
		parts := make([]string, v.Len())
		for i := range parts {
			parts[i] = dump(v.Index(i), depth+1)
		}
		return "[" + strings.Join(parts, ",") + "]"
	case reflect.Map:
		if v.IsNil() {
			return "nilmap"
		}
		var parts []string
		it := v.MapRange()
		for it.Next() {
			parts = append(parts, dump(it.Key(), depth+1)+"=>"+dump(it.Value(), depth+1))
		}
		sort.Strings(parts)
		return "map{" + strings.Join(parts, ",") + "}"
	case reflect.Float32, reflect.Float64:
		return strconv.FormatFloat(v.Float(), 'g', -1, 64)
	case reflect.String:
		return strconv.Quote(v.String())
	default:
		if v.CanInterface() {
			return fmt.Sprintf("%v", v.Interface())
		}
		return fmt.Sprintf("<%s>", v.Kind())
	}
}

// fill writes seeded random values into v.
func fill(v reflect.Value, r *rand.Rand, depth int) {
	if depth > 4 || !v.CanSet() {
		return
	}
	switch v.Kind() {
	case reflect.Pointer:
		if r.Intn(4) == 0 {
			return
		}
		p := reflect.New(v.Type().Elem())
		fill(p.Elem(), r, depth+1)
		v.Set(p)
	case reflect.Struct:
		if v.Type().String() == "time.Time" {
			v.Set(reflect.ValueOf(timeOf(r)))
			return
		}
		for i := 0; i < v.NumField(); i++ {
			if v.Type().Field(i).IsExported() || v.Type().Field(i).Anonymous {
				fill(v.Field(i), r, depth+1)
			}
		}
	case reflect.Slice:
		if r.Intn(4) == 0 {
			return
		}
		n := r.Intn(3)
		s := reflect.MakeSlice(v.Type(), n, n)
		for i := 0; i < n; i++ {
			fill(s.Index(i), r, depth+1)
		}
		v.Set(s)
	case reflect.Array:
		for i := 0; i < v.Len(); i++ {
			fill(v.Index(i), r, depth+1)
		}
	case reflect.Map:
		if r.Intn(4) == 0 {
			return
		}
		m := reflect.MakeMap(v.Type())
		for i := 0; i < r.Intn(3); i++ {
			k := reflect.New(v.Type().Key()).Elem()
			fill(k, r, depth+1)
			e := reflect.New(v.Type().Elem()).Elem()
			fill(e, r, depth+1)
			m.SetMapIndex(k, e)
		}
		v.Set(m)
	case reflect.Interface:
		choices := []any{nil, 1, "s", 1.5, []any{"a", 2}, map[string]any{"k": true}}
		c := choices[r.Intn(len(choices))]
		if c != nil {
			v.Set(reflect.ValueOf(c))
		}
	case reflect.String:
		strs := []string{"", "a", "Hé", "\xff", "<&>", " ", "12", "true"}
		if v.Type().String() == "json.Number" {
			strs = []string{"", "12", "1.5e3", "x", "-0"}
		}
		v.SetString(strs[r.Intn(len(strs))])
	case reflect.Bool:
		v.SetBool(r.Intn(2) == 0)
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		v.SetInt([]int64{0, 1, -1, 127, -128}[r.Intn(5)])
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		v.SetUint([]uint64{0, 1, 255}[r.Intn(3)])
	case reflect.Float32, reflect.Float64:
		fs := []float64{0, 1.5, -2.25, 1e21, 1e-7, 3.4e38}
		v.SetFloat(fs[r.Intn(len(fs))])
	}
}

func errType(err error) string {
	if err == nil {
		return "ok"
	}
	return fmt.Sprintf("%T", err)
}

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		f := strings.Split(sc.Text(), "\t")
		id, ti, mode, arg := f[0], f[1], f[2], f[3]
		i, _ := strconv.Atoi(ti)
		res := func() (out string) {
			defer func() {
				if p := recover(); p != nil {
					out = "PANIC:" + strings.SplitN(fmt.Sprint(p), "\n", 2)[0]
				}
			}()
			v := factories[i]()
			switch mode {
			case "fresh", "prefill":
				if mode == "prefill" {
					fill(reflect.ValueOf(v).Elem(), rand.New(rand.NewSource(int64(i)*7919)), 0)
				}
				data, _ := base64.StdEncoding.DecodeString(arg)
				err := json.Unmarshal(data, v)
				return errType(err) + " | " + dump(reflect.ValueOf(v).Elem(), 0)
			default:
				seed, _ := strconv.Atoi(arg)
				fill(reflect.ValueOf(v).Elem(), rand.New(rand.NewSource(int64(seed)*104729+int64(i))), 0)
				b, err := json.Marshal(v)
				return errType(err) + " | " + string(b)
			}
		}()
		fmt.Fprintf(w, "%s\t%s\n", id, res)
	}
}

func timeOf(r *rand.Rand) time.Time {
	return time.Date(2000+r.Intn(30), time.Month(1+r.Intn(12)), 1+r.Intn(28), r.Intn(24), 0, 0, 0, time.UTC)
}
