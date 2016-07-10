#!/usr/bin/python

"""
Modify some pictures.
"""

from subprocess import call
import argparse
import datetime
import glob
import os.path
import re

EXTENSION_RE = re.compile(r'(^[^-]+-[^-]+-.*)\.jpg$')

def rotate_images(filenames, degrees, dryrun):
    """Rotate images by degrees.

    If dryrun is True, just print what we would have done.
    """
    for filename in filenames:
        components = EXTENSION_RE.match(filename)
        basename = components.groups()[0]
        orig_file = basename + '.jpg.orig'
        if os.path.isfile(orig_file):
            print('{of} exists, not making further backup'.format(of=orig_file))
        if dryrun:
            print('{deg}: {fn}'.format(fn=filename,
                                       deg=degrees))
        else:
            call(['/bin/mv', filename, orig_file])
            call(['convert', '-quality', '100', '-rotate', str(degrees), orig_file, filename])

# filename_re = re.compile('(^[^-]+)-([^-]+)-(.*)\.(jpg|cr2|raf)$')
FILENAME_RE = re.compile(r'(^[^-]+-[^-]+)-(.*)\.(.*)$')
DATETIME_FORMAT = '%Y%m%d-%H%M%S'

def time_shift_images(filenames, hours, dryrun):
    """Time shift image names by hours.

    If dryrun is True, just print what we would have done.
    """
    num_processed = 0
    seconds = hours * 3600
    time_delta = datetime.timedelta(seconds=seconds)
    for filename in filenames:
        components = FILENAME_RE.match(filename)
        datetime_string = components.groups()[0]
        sequence_string = components.groups()[1]
        image_datetime = datetime.datetime.strptime(datetime_string, DATETIME_FORMAT)
        image_datetime += time_delta
        new_datetime_string = datetime.datetime.strftime(image_datetime, DATETIME_FORMAT)
        variants = glob.glob('{ds}-{ss}.*'.format(ds=datetime_string, ss=sequence_string))
        for variant in variants:
            extension = FILENAME_RE.match(variant).groups()[2]
            new_filename = '{ds}-{sn}.{ext}'.format(ds=new_datetime_string,
                                                    sn=sequence_string,
                                                    ext=extension)
            num_processed += 1
            if dryrun:
                print('{fn} -> {nfn}'.format(fn=variant, nfn=new_filename))
            else:
                call(['/bin/mv', '-i', variant, new_filename])
    print('Processed {np} files'.format(np=num_processed))

def main():
    """Do what we do."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='+',
                        help='Files on which to operate.  Will find all files with same basename.',
                        type=str)
    parser.add_argument('--time',
                        help='Offset, in hours, by which to adjust time embedded in filename',
                        type=float)
    parser.set_defaults(time=0)
    parser.add_argument('--rot',
                        help='Rotate images (90, 180, 270)',
                        type=int)
    parser.set_defaults(rot=0)
    parser.add_argument('--dryrun',
                        help="Don't do anything but say what we would have done",
                        dest='dryrun', action='store_true')
    parser.set_defaults(dryrun=False)
    args = parser.parse_args()
    if args.rot != 0:
        rotate_images(args.filename, args.rot, args.dryrun)
    if args.time != 0:
        time_shift_images(args.filename, args.time, args.dryrun)

if __name__ == "__main__":
    main()
