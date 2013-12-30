#!/bin/bash

## This install file is pretty custom.
## Modify to suit your site.

TO_BIN='pic-new
    pic_select.py
    pic-small
'
echo cp $TO_BIN "$HOME/bin/"

# This works with my dotfiles setup.
cp pic-bash.sh $HOME/.dotfiles/bash/pictools
