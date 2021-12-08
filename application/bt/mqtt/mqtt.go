package mqtt

import (
	"fmt"
	"strings"

	paho "github.com/eclipse/paho.mqtt.golang"
)

var messageSubHandler paho.MessageHandler = func(client paho.Client, msg paho.Message) {
	fmt.Println(string(msg.Payload()))
}

type boo struct {
}

func (b boo) yeah(client paho.Client, msg paho.Message) {
	fmt.Println(string(msg.Payload()))
}

var messageListenHandler paho.MessageHandler = func(client paho.Client, msg paho.Message) {
	fmt.Println(string(msg.Payload()))

}

var connectHandler paho.OnConnectHandler = func(client paho.Client) {
	fmt.Println("Connected")
}

var connectLostHandler paho.ConnectionLostHandler = func(client paho.Client, err error) {
	fmt.Printf("Connect lost: %v", err)
}

func Sub(client paho.Client) {
	topic := "to-app"
	// token := client.Subscribe(topic, 1, messageSubHandler)
	b := boo{}
	token := client.Subscribe(topic, 1, b.yeah)
	token.Wait()
	fmt.Println("Subscribed to topic:", topic)
}

func Listen(handler paho.MessageHandler, client paho.Client) {
	topic := "to-app"
	token := client.Subscribe(topic, 1, handler)
	token.Wait()
	fmt.Println("Subscribed to topic:", topic)
}

func Pub(client paho.Client, args []string) {
	msg := strings.Join(args, ", ")
	topic := "from-app"
	token := client.Publish(topic, 1, true, msg)
	token.Wait()
	fmt.Println("Published message:", msg)
}

func set(opts *paho.ClientOptions, broker string) {
	fmt.Println("Initializing client options")
	var port = 1883
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", broker, port))
	opts.OnConnect = connectHandler
	opts.OnConnectionLost = connectLostHandler
}

func GetClient(broker string) (client paho.Client) {
	opts := paho.NewClientOptions()
	set(opts, broker)
	client = paho.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	return
}
