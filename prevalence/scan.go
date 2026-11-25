package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"reflect"
	"strings"
)

type counts struct {
	MapKeyWithUnmarshalJSON int // #83391
	NumberWithString        int // #83392
	TextTypeWithString      int // #83392 generalization
	StringOption            int // exposure: any ,string tag
	TimeFieldJSON           int // exposure for #83393/#83395: time.Time in json-tagged struct
	MethodFieldJSON         int // exposure for #83395: field whose type has UnmarshalJSON/UnmarshalText
	FloatKeyMap             int // #81373
	IfaceEmbedsMarshaler    int // #82682
	ImportsJSON             bool
}

func typName(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.Ident:
		return t.Name
	case *ast.StarExpr:
		return typName(t.X)
	case *ast.SelectorExpr:
		if x, ok := t.X.(*ast.Ident); ok {
			return x.Name + "." + t.Sel.Name
		}
	}
	return ""
}

func main() {
	root := os.Args[1]
	var files []*ast.File
	fset := token.NewFileSet()
	filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() && (info.Name() == "vendor" || info.Name() == "testdata" || strings.HasPrefix(info.Name(), ".")) {
			return filepath.SkipDir
		}
		if strings.HasSuffix(p, ".go") && !strings.HasSuffix(p, "_test.go") {
			if f, err := parser.ParseFile(fset, p, nil, parser.SkipObjectResolution); err == nil {
				files = append(files, f)
			}
		}
		return nil
	})
	ujson, utext := map[string]bool{}, map[string]bool{}
	for _, f := range files {
		for _, d := range f.Decls {
			fd, ok := d.(*ast.FuncDecl)
			if !ok || fd.Recv == nil || len(fd.Recv.List) == 0 {
				continue
			}
			n := typName(fd.Recv.List[0].Type)
			if fd.Name.Name == "UnmarshalJSON" {
				ujson[n] = true
			}
			if fd.Name.Name == "UnmarshalText" {
				utext[n] = true
			}
		}
	}
	var c counts
	for _, f := range files {
		for _, im := range f.Imports {
			if im.Path.Value == `"encoding/json"` {
				c.ImportsJSON = true
			}
		}
		ast.Inspect(f, func(n ast.Node) bool {
			switch t := n.(type) {
			case *ast.MapType:
				k := typName(t.Key)
				if ujson[k] {
					c.MapKeyWithUnmarshalJSON++
				}
				if k == "float64" || k == "float32" {
					c.FloatKeyMap++
				}
			case *ast.InterfaceType:
				for _, m := range t.Methods.List {
					if len(m.Names) == 0 {
						if s := typName(m.Type); s == "json.Marshaler" || s == "json.Unmarshaler" {
							c.IfaceEmbedsMarshaler++
						}
					}
				}
			case *ast.StructType:
				for _, fl := range t.Fields.List {
					if fl.Tag == nil {
						continue
					}
					tag := reflect.StructTag(strings.Trim(fl.Tag.Value, "`")).Get("json")
					if tag == "" {
						continue
					}
					tn := typName(fl.Type)
					hasStr := false
					for _, o := range strings.Split(tag, ",")[1:] {
						if o == "string" {
							hasStr = true
						}
					}
					if hasStr {
						c.StringOption++
						if tn == "json.Number" {
							c.NumberWithString++
						}
						if utext[tn] {
							c.TextTypeWithString++
						}
					}
					if tn == "time.Time" {
						c.TimeFieldJSON++
					}
					if ujson[tn] || utext[tn] {
						c.MethodFieldJSON++
					}
				}
			}
			return true
		})
	}
	b, _ := json.Marshal(c)
	fmt.Println(string(b))
}
