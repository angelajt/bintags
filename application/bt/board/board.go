package board

type Board struct {
	Id       string
	Ordernum string
	Status   string
}

func NewBoard(id string, ordernum string, status string) (b Board) {
	b = Board{Id: id, Ordernum: ordernum, Status: status}
	return
}
