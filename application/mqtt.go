package main

import (
	"fmt"
	"os"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

var messageSubHandler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	fmt.Println(string(msg.Payload()))
}

var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Connected")
}

var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Connect lost: %v", err)
}

func main() {
	opts := mqtt.NewClientOptions()
	broker := os.Args[1]
	set(opts, broker)
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	sub(client)
	//	publish(client)

	time.Sleep(time.Second * 1000)

	client.Disconnect(250)
}

func sub(client mqtt.Client) {
	topic := "to-app"
	token := client.Subscribe(topic, 1, messageSubHandler)
	token.Wait()
	fmt.Println("Subscribed to topic:", topic)
}

func set(opts *mqtt.ClientOptions, broker string) {
	fmt.Println("Initializing client options")
	var port = 1883
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler
}
