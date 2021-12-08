package board

import "bt/mqtt"

type Board struct {
	Id       string
	Ordernum string
	Status   string
}

func NewBoard(id string, ordernum string, status string) (b Board) {
	b = Board{Id: id, Ordernum: ordernum, Status: status}
	return
}

func (b Board) Reset(broker, ordernum string) {
	b.Ordernum = ordernum
	client := mqtt.GetClient(broker)
	args := []string{b.Id, b.Ordernum}
	mqtt.Pub(client, args)
}
