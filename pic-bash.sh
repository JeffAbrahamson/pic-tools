# Some useful bash aliases, to source from .bashrc, for example

# I don't like to type .py, but the .py permits generation of .pyc's.
alias pic-mod=pic_mod.py

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

# ufraw with favorite options.
ufr() {
    base=$(basename $1 .jpg);
    if [ -r $base.raf ]; then
	infile="$base.raf";	# What I generate now.
    elif [ -r $base.cr2 ]; then
	infile="$base.cr2";	# What I used to generate.
    else
	echo "Input file '$base' missing?"
	infile="$base.cr2"	# Will trigger existence check failure.
    fi
    outfile="$base-2.jpg";
    if [ ! -r "$infile" -o -e "$outfile" ]; then
        echo "Existence check failed.";
    else
        ufraw --create-id=also "$infile" --output="$outfile";
    fi
}

# ufraw-batch with favorite options.
ufb() {
    base=$(basename $1 .jpg);
    if [ -r $base.raf ]; then
	infile="$base.raf";	# What I generate now.
    elif [ -r $base.cr2 ]; then
	infile="$base.cr2";	# What I used to generate.
    else
	echo "Input file '$base' missing?"
	infile="$base.cr2"	# Will trigger existence check failure.
    fi
    outfile="$base-2.jpg";
    if [ ! -r "$infile" -o -e "$outfile" ]; then
	echo "Existence check failed."
    else
	ufraw-batch --create-id=also "$infile" --output="$outfile"
    fi
}

# Add a file to the current pic-select selection.  I should quite
# pic-select before using this, since pic-select thinks it is alone in
# the world: it will ruthlessly overwrite its data file on changes
# that it initiates.
pic-add-to-selection() {
    new_image="$1"
    select_base="${2:-best}"
    select_active="${select_base}.txt"
    select_active_backup="${select_active}.bak"
    select_all="${select_base}.txt-orig"
    select_all_backup="${select_all}.bak"
    mv "$select_active" "$select_active_backup"
    mv "$select_all" "$select_all_backup"
    (echo $new_image; cat $select_active_backup) | sort -u > "$select_active"
    (echo $new_image; cat $select_all_backup) | sort -u > "$select_all"
}

# Create or update a shadow directory of images.
# The argument is the image source directory.
# For each jpg image in the image source directory that does not exist
# in the current directory, make a copy at 1920 x 1200 in the current
# directory.  Make symbolic links in the current directory to any
# *txt* files in the source directory.  Create a local symlink "orig"
# pointing to the source images.
#
# This will break if image file names contain spaces.
#
# This was useful when I was using a machine that was too weak to
# display images quickly at full size.  It is probably of decreasing
# interest.
pic-make-shadow() {
    _source="$1"
    if [ X = "X$_source" -a -e orig ]; then
	# If the orig/ symlink exists, then I probably want to use that and do an update.
	_source=$(stat --format='%N' orig | sed -e "s/^.*>//; s/^ ‘//; s/’$//")
    fi
    if [ ! -d "$_source" ]; then
	echo "Directory \"$_source\" does not exist."
	return
    fi
    _image_files=$(cd "$_source"; /bin/ls *jpg)
    for f in $_image_files; do
	if [ ! -e "$f" -o "orig/$f" -nt "$f" ]; then
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

    if [ ! -e orig ]; then
	ln -s "$_source" orig
    fi
    # Use the checksum flag in order to avoid updating time with
    # --update and then copying both ways.
    echo "Copying text files to orig/"
    rsync -v --checksum --update --exclude='*~' *txt* orig/
    echo "Copying text files from orig/"
    rsync -v --checksum --update --exclude='*~' orig/*txt* ./
}
