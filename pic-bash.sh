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

# Create or update a shadow directory of images.
# The argument is the image source directory.
# For each jpg image in the image source directory that does not exist
# in the current directory, make a copy at 1920 x 1200 in the current
# directory.  Make symbolic links in the current directory to any
# *txt* files in the source directory.  Create a local symlink "orig"
# pointing to the source images.
#
# This will break if image file names contain spaces.
pic-make-shadow() {
    _source="$1"
    if [ ! -d "$_source" ]; then
	echo "Directory \"$_source\" does not exist."
	return
    fi
    _image_files=$(cd "$_source"; /bin/ls *jpg)
    for f in $_image_files; do
	if [ ! -e "$f" ]; then
	    echo $f
	    convert -geometry 1920x1200 "$_source/$f" "$f"
	fi
    done
    _local_images=$(/bin/ls *jpg 2>/dev/null)
    for f in $_local_images; do
	if [ ! -e "$_source/$f" ]; then
	    echo "$f is missing in orig/"
	fi
    done

    _local_text_files=$(/bin/ls *txt* 2>/dev/null)
    for f in $_local_text_files; do
	if [ ! -e "$_source/$f" ]; then
	    cp "$f" "$_source/$f"
	fi
    done
    _text_files=$(cd "$_source"; /bin/ls *txt* 2>/dev/null)
    for f in $_text_files; do
	if [ ! -e "$f" ]; then
	    ln -s "$_source/$f" "$f"
	fi
    done
    if [ ! -e orig ]; then
	ln -s "$_source" orig
    fi
}
