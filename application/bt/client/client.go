package client

import (
	"bt/config"
	"bt/mqtt"
	"fmt"

	paho "github.com/eclipse/paho.mqtt.golang"
)

func Pub(conf *config.Conf, args []string) {
	client := mqtt.GetClient(conf.Broker)

	done := make(chan string)
	resHandler := func(client paho.Client, msg paho.Message) {
		done <- string(msg.Payload())
	}

	mqtt.Listen(resHandler, client, "res")

	mqtt.Pub(client, "cmd", args)
	out := <-done
	fmt.Println(out)
}
