DIT_DIR = ~/.dit

BIN_DIR = ~/bin

.PHONY: install fetcher conf spend

install: fetcher conf spend

fetcher: fetcher.py
	ln -sf $(PWD)/fetcher.py  $(DIT_DIR)/.fetcher

spend: spend.py
	ln -sf $(PWD)/spend.py    $(BIN_DIR)/dit-spend

conf: gitlab.conf
	ln -sf $(PWD)/gitlab.conf $(DIT_DIR)/.gitlab.conf
