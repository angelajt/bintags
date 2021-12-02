package db

import "bt/board"

func Get(boardid string) (b board.Board) {
	b = board.NewBoard(boardid, "none", "unreal")

	return
}
