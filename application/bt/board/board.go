package board

import "bt/mqtt"

type Board struct {
	id       string
	ordernum string
	status   string
}

func NewBoard(id string, ordernum string, status string) (b Board) {
	b = Board{id: id, ordernum: ordernum, status: status}
	return
}

func (b Board) Reset(broker, ordernum string) {
	b.ordernum = ordernum
	client := mqtt.GetClient(broker)
	args := []string{b.id, b.ordernum}
	mqtt.Pub(client, args)
}
