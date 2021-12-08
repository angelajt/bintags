package server

import (
	"bt/board"
	"bt/db"
	"bt/mqtt"
	"flag"
	"fmt"
	"strconv"
	"strings"
	"time"

	paho "github.com/eclipse/paho.mqtt.golang"
)

type Message struct {
	src      string
	dst      string
	counter  int
	ordernum string
	status   string
}

func parseMessage(txt string) (m *Message) {
	data := strings.Split(txt, ", ")
	if len(data) < 6 {
		fmt.Println("garbage message:", txt)
		return
	}
	counter, err := strconv.Atoi(data[3])
	if err != nil {
		fmt.Println("garbage counter:", txt)
		return
	}
	m = &Message{
		src:      data[1],
		dst:      data[2],
		counter:  counter,
		ordernum: data[4],
		status:   data[5],
	}
	return
}

type Server struct {
	rxQueue chan Message
}

func (s *Server) rxHandler(client paho.Client, msg paho.Message) {
	m := parseMessage(string(msg.Payload()))
	if m != nil {
		fmt.Println("adding to the queue", *m)
		s.rxQueue <- *m
		fmt.Println("addED to the queue", *m)
	}
}

func Monitor(args []string) {
	broker := args[0]
	client := mqtt.GetClient(broker)

	mqtt.Sub(client)

	time.Sleep(time.Second * 1000)

	client.Disconnect(250)
}

func Serve(args []string) {
	flag.CommandLine.Parse(args)
	broker := args[0]
	repository := args[1]
	client := mqtt.GetClient(broker)

	d := db.NewDb(repository)
	defer d.Close()

	server := Server{}
	server.rxQueue = make(chan Message, 999)

	mqtt.Listen(server.rxHandler, client)
	fmt.Println("yeahh")

	for {
		time.Sleep(time.Millisecond * 100)
		if len(server.rxQueue) > 0 {
			fmt.Println("the queue has stuff in it")
			msg := <-server.rxQueue
			err := process(d, msg)
			if err != nil {
				fmt.Println("bad message:", msg)
			}
		}
	}
	// client.Disconnect(250)
}

func process(d *db.Db, msg Message) (err error) {
	b := board.Board{
		Id:       msg.src,
		Ordernum: msg.ordernum,
		Status:   msg.status,
	}
	err = d.Update(b)
	if err != nil {
		return
	}
	fmt.Println("yehahhh", msg)
	return
}

func Pub(args []string) {
	broker := args[0]
	client := mqtt.GetClient(broker)
	data := args[1:]

	mqtt.Pub(client, data)
}

func Reset(args []string) {
	broker := args[0]
	// repository := args[1]
	boardid := args[2]
	ordernum := args[3]
	board := db.Get(boardid)
	board.Reset(broker, ordernum)
}
