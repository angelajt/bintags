package main

import (
	"encoding/json"
	"fmt"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type Payload struct {
	Object struct {
		DecodeDataString string `json:"DecodeDataString"`
	} `json:"object"`
}

/*
var messagePubHandler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	fmt.Printf("Received message: %s from topic: %s\n", msg.Payload(), msg.Topic())
}
*/

var messageSubHandler mqtt.MessageHandler = func(client mqtt.Client, msg mqtt.Message) {
	var p Payload
	err := json.Unmarshal(msg.Payload(), &p)
	if err != nil {
		return
	}
	fmt.Println(p.Object.DecodeDataString)
}

var connectHandler mqtt.OnConnectHandler = func(client mqtt.Client) {
	fmt.Println("Connected")
}

var connectLostHandler mqtt.ConnectionLostHandler = func(client mqtt.Client, err error) {
	fmt.Printf("Connect lost: %v", err)
}

func main() {
	opts := mqtt.NewClientOptions()
	set(opts)
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	sub(client)
	//	publish(client)

	time.Sleep(time.Second * 1000)

	client.Disconnect(250)
}

/*
func publish(client mqtt.Client) {
	num := 10
	for i := 0; i < num; i++ {
		text := fmt.Sprintf("Message %d", i)
		token := client.Publish("application/4/#", 0, false, text)
		token.Wait()
		time.Sleep(time.Second)
	}
}*/

func sub(client mqtt.Client) {
	topic := "application/4/#"
	token := client.Subscribe(topic, 1, messageSubHandler)
	token.Wait()
	fmt.Println("Subscribed to topic:", topic)
}

func set(opts *mqtt.ClientOptions) {
	fmt.Println("Initializing client options")
	var broker = "rak-gateway.local"
	var port = 1883
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	// opts.SetDefaultPublishHandler(messagePubHandler)
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler
}
