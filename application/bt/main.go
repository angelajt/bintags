package main

import (
	"bt/client"
	"bt/config"
	"bt/server"
	"fmt"
	"os"
	"path"
)

func main() {
	home := os.Getenv("HOME")
	conffn := path.Join(home, ".btconfig.json")
	conf, err := config.Load(conffn)
	if err != nil {
		panic(err)
	}
	fmt.Println(conf)

	cmd := os.Args[1]
	args := os.Args[2:]
	switch cmd {
	case "serve":
		server.Serve(conf, args)
	case "monitor":
		server.Monitor(conf, args)
	default:
		client.Pub(conf, os.Args[1:])
	}
}
