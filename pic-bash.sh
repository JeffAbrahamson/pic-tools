# Some useful bash aliases, to source from .bashrc, for example

pic-dates() {
    if [ "X$1" = X ]; then
	for d in $(find .  -maxdepth 1 -type d -o -type l); do
	    echo $d
	    pic-dates "$d/" | perl -pwe 's/^/   /;'
	done
    else
	ls "$1" | perl -pwe 's/-.*$//;' | uniq | grep -v txt;
    fi
}
pic-select() { pic_select.py $1; }
