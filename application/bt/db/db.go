package db

import (
	"bt/board"
	"context"
	"database/sql"
	"fmt"
	"time"

	_ "github.com/mithrandie/csvq-driver"
	"github.com/mithrandie/csvq/lib/query"
)

type Db struct {
	path string
	csvq *sql.DB
}

func NewDb(path string) (db *Db) {
	db = &Db{path: path}
	var err error
	db.csvq, err = sql.Open("csvq", path)
	if err != nil {
		panic(err)
	}
	return
}

func (db *Db) Close() {
	if err := db.csvq.Close(); err != nil {
		panic(err)
	}
}

func (db *Db) Update(b board.Board) (err error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	_, err = get(ctx, db.csvq, b.Id)
	if err != nil {
		err = insert(ctx, db.csvq, b)
		return
	}

	err = update(ctx, db.csvq, b)
	if err != nil {
		panic(err)
	}
	return
}

func get(ctx context.Context, db *sql.DB, id string) (b board.Board, err error) {
	queryString := fmt.Sprintf("SELECT board, num, status FROM `bintags.csv` WHERE board = '%s'", id)
	fmt.Println(queryString)
	r := db.QueryRowContext(ctx, queryString)
	b, err = ScanRow(r)
	if err != nil {
		return
	}
	return
}

func ScanRow(r *sql.Row) (b board.Board, err error) {
	b = board.Board{}
	err = r.Scan(&b.Id, &b.Ordernum, &b.Status)
	if err != nil {
		if err == sql.ErrNoRows {
			return
		} else if csvqerr, ok := err.(query.Error); ok {
			panic(fmt.Sprintf("Unexpected error: Number: %d  Message: %s", csvqerr.Number(), csvqerr.Message()))
		} else {
			panic("Unexpected error: " + err.Error())
		}
	}
	return
}

func update(ctx context.Context, db *sql.DB, b board.Board) (err error) {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	queryString := fmt.Sprintf("UPDATE `bintags.csv` SET num = '%s', status = '%s' WHERE board = '%s'", b.Ordernum, b.Status, b.Id)
	ret, err := tx.ExecContext(ctx, queryString)

	affected, _ := ret.RowsAffected()
	fmt.Printf("rows changed: %d\n", affected)

	if err != nil {
		if e := tx.Rollback(); e != nil {
			panic(e.Error())
		}
		return err
	}

	if e := tx.Commit(); e != nil {
		panic(e.Error())
	}
	return
}

func insert(ctx context.Context, db *sql.DB, b board.Board) (err error) {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		panic(err)
	}
	queryString := fmt.Sprintf("INSERT INTO `bintags.csv` (board, num, status) VALUES ('%s', '%s', '%s')", b.Id, b.Ordernum, b.Status)

	ret, err := tx.ExecContext(ctx, queryString)

	affected, _ := ret.RowsAffected()
	fmt.Printf("rows inserted: %d\n", affected)

	if err != nil {
		if e := tx.Rollback(); e != nil {
			panic(e.Error())
		}
		return err
	}

	if err := tx.Commit(); err != nil {
		return err
	}
	return
}

func Get(boardid string) (b board.Board) {
	b = board.NewBoard(boardid, "none", "unreal")

	return
}
