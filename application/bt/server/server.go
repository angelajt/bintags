package server

import (
	"bt/board"
	"bt/config"
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

func parseRx(txt string) (m *Message) {
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

func processCmd(client paho.Client, d *db.Db, txt string) (err error) {
	args := strings.Split(txt, ", ")
	cmd := args[0]
	switch cmd {
	case "reset":
		if len(args) < 3 {
			fmt.Println("why")
			return
		}
		b := board.Board{
			Id:       args[1],
			Ordernum: args[2],
			Status:   "created",
		}

		err = d.Update(b)
		if err != nil {
			return
		}

		mqtt.Pub(client, "from-app", args[1:])
		mqtt.Pub(client, "res", append(args[1:], "reset"))
	}
	return
}

type Server struct {
	rxQueue  chan Message
	cmdQueue chan string
}

func (s *Server) rxHandler(client paho.Client, msg paho.Message) {
	m := parseRx(string(msg.Payload()))
	if m != nil {
		fmt.Println("adding to the queue", *m)
		s.rxQueue <- *m
		fmt.Println("addED to the queue", *m)
	}
}

func (s *Server) cmdHandler(client paho.Client, msg paho.Message) {
	m := string(msg.Payload())
	fmt.Println("adding to the queue", m)
	s.cmdQueue <- m
	fmt.Println("addED to the queue", m)
}

func Monitor(conf *config.Conf, args []string) {
	client := mqtt.GetClient(conf.Broker)

	mqtt.Sub(client)

	time.Sleep(time.Second * 1000)

	client.Disconnect(250)
}

func Serve(conf *config.Conf, args []string) {
	flag.CommandLine.Parse(args)
	client := mqtt.GetClient(conf.Broker)

	d := db.NewDb(conf.Repository)
	defer d.Close()

	server := Server{}
	server.rxQueue = make(chan Message, 999)
	server.cmdQueue = make(chan string, 999)

	mqtt.Listen(server.rxHandler, client, "to-app")
	mqtt.Listen(server.cmdHandler, client, "cmd")

	for {
		time.Sleep(time.Millisecond * 100)
		if len(server.rxQueue) > 0 {
			fmt.Println("the rxQueue has stuff in it")
			msg := <-server.rxQueue
			_, err := processBoard(d, msg)
			if err != nil {
				fmt.Println("bad message:", msg)
			}
		}
		if len(server.cmdQueue) > 0 {
			fmt.Println("the cmdQueue has stuff in it")
			msg := <-server.cmdQueue
			err := processCmd(client, d, msg)
			if err != nil {
				fmt.Println("bad command:", msg)
			}
		}
	}
	// client.Disconnect(250)
}

/*
func List(args []string) {
	var boards []board.Board
	if len(args) == 0 {
		boards = db.GetAll()
	}
	for b := range boards {
		fmt.Println(b)
	}
}
*/
func processBoard(d *db.Db, msg Message) (b board.Board, err error) {
	b = board.Board{
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
