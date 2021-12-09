package config

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
)

type Conf struct {
	Broker     string
	Repository string
}

func Load(fn string) (conf *Conf, err error) {
	fmt.Println("loading")
	buf, err := ioutil.ReadFile(fn)
	if err != nil {
		return
	}

	conf = &Conf{}
	err = json.Unmarshal(buf, conf)
	fmt.Println(conf)
	if err != nil {
		return
	}
	return
}
