package server

import (
	"bt/db"
	"bt/mqtt"
	"time"
)

func Monitor(args []string) {
	broker := args[0]
	client := mqtt.GetClient(broker)

	mqtt.Sub(client)
	//	publish(client)

	time.Sleep(time.Second * 1000)

	client.Disconnect(250)
}

func Pub(args []string) {
	broker := args[0]
	client := mqtt.GetClient(broker)
	data := args[1:]

	mqtt.Pub(client, data)
}

func Reset(args []string) {
	broker := args[0]
	boardid := args[1]
	ordernum := args[2]
	board := db.Get(boardid)
	board.Reset(broker, ordernum)
}
