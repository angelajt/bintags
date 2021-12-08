package main

import (
	"bt/server"
	"os"
)

func main() {
	cmd := os.Args[1]
	args := os.Args[2:]
	switch cmd {
	case "serve":
		server.Serve(args)
	// move these to the cmd topic message handler
	case "monitor":
		server.Monitor(args)
	case "pub":
		server.Pub(args)
	case "reset":
		server.Reset(args)
		//default:
		//	client.Pub(os.Args[1:])
	}
}
