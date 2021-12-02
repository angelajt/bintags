package main

import (
	"bt/server"
	"os"
)

func main() {
	cmd := os.Args[1]
	args := os.Args[2:]
	switch cmd {
	case "monitor":
		server.Monitor(args)
	case "pub":
		server.Pub(args)
	case "reset":
		server.Reset(args)
	}
}
