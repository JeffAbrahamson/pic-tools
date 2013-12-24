BIN=$(HOME)/bin/

BINS =			\
	pic-small	\
	pic-new		\
	pic_select.py	\


install : $(BINS)
	for f in $(BINS); do /bin/cp -f $$f $(BIN)/; done
	cp pic-bash.sh $(HOME)/.dotfiles/bash/pictools
