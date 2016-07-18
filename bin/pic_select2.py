#!/usr/bin/python


"""A utility to select images using dmenu for control.

Search for files named select.[0-5d].  Their meanings are
  - select.0 - images that have not been classed
  - select.1 - images to keep but not exceptional, eventually ok to discard the raw images
  - select.2 - images that are reasonably good
  - select.3 - images that are very good
  - select.4 - images that are exceptional
  - select.5 - images that are super exceptional, among the best I've taken
  - select.d - images that I should delete

If those files don't exist, they are created (empty) except for
select.0 which is created from globbing *.jpg.

Enter a loop using dmenu and displaying (via geeqie) the first image
from select.0 if it is non-empty, else requesting the quality level to
use.

Display images from the requested selection.  Prompt via dmenu for a
new classification.  On classifying, add the filename to the requested
selection file and remove from the old one.

If the user responds with q, quit the program.

If the user responds with z, suspend the program (meaning don't
relaunch dmenu until indicated at the terminal, since dmenu grabs the
keyboard and so prevents interacting with other programs.

If the user responds with s, run pic-small on the image.

"""

GPL = """
Copyright 2016  Jeff Abrahamson

This file is part of pic utilities.

pic_select2.py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

pic_select is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pic_select2.py.  If not, see
<http://www.gnu.org/licenses/>.  
"""

import argparse
import time
import subprocess
import sys

def read_file(filename):
    """Read file filename and return an array of lines.

    Lines are stripped of trailing newline.
    """
    try:
        with open(filename, 'r') as f_ptr:
            lines = f_ptr.read().splitlines()
    except:
        #print "Failed to read " + filename + ".  Continuing as empty."
        return []
    return lines
            
def write_file(filename, data):
    """Write data to file filename.

    Data is an array, elements of which are written separated by
    newline characters.
    """
    with open(filename, 'w') as f_ptr:
        for line in data:
            f_ptr.write(line + "\n")

class ImageFiles:
    """Track our decisions thus far, and encapsulate how to behave."""

    main_name = ''
    main = []
    main_index = 0
    status = ''

    selection_0 = 'selection.0'
    selection_1 = 'selection.1'
    selection_2 = 'selection.2'
    selection_3 = 'selection.3'
    selection_4 = 'selection.4'
    selection_5 = 'selection.5'
    selection_d = 'selection.d'
    collection_names = {'0': selection_0,
                        '1': selection_1,
                        '2': selection_2,
                        '3': selection_3,
                        '4': selection_4,
                        '5': selection_5,
                        'd': selection_d}

    def __init__(self):
        """Initialize collections."""
        self.collections = {}   # Map selection name to set of images (the selection).
        if not os.path.isfile(selection_0):
            print('Initializing selection 0.')
            filenames = glob.glob('*.jpg')
            write_file(selection_0, filenames)
        for selection_name in collection_names.values():
            if os.path.isfile(selection):
                self.collections[selection] = set(read_file(selection_name))
            else:
                self.collections[selection] = set()
        if len(self.collections[selection_0]) > 0:
            self.current_selection = selection_0
        else:
            self.current_selection = selection_1
        self.current_index = min(0, len(self.collections[self.current_selection]) - 1)
        self.traversal = list(self.collections[self.current_selection])
        self.traversal.sort()
        sleep(1)                # Let me move to the write workspace
                                # and window in case it's not this
                                # one.

    def current_selection_empty(self):
        """Return True if the current selection is empty, False otherwise."""
        return len(self.collections[self.current_selection]) == 0

    def update_display(self):
        """Update the image and metadata displays."""
        self.update_status(stdscr)
        self.display_image()

    def display_image(self):
        """Display the current image."""
        # geeqie --remote view 
        if self.current_selection_empty()
            return
        subprocess.call(['geeqie', '--remote', 'file:', \
                         self.traversal[self.current_index]])

    def update_status(self):
        """Update the status message."""
        stdscr.clear()
        num_accepted = len(self.accepted)
        num_rejected = len(self.rejected)
        num_orig = len(self.orig)
        num_remaining = len(self.main)
        if num_rejected + num_accepted > 0:
            frac_accepted = 100.0 * num_accepted / (
                num_rejected + num_accepted)
            frac_remaining = 100.0 * num_remaining / num_orig
        else:
            frac_accepted = 0
            frac_remaining = 100.0
        message = ('Current={cur} / Accepted={acc} ({acc_pct:.0f}%) / Rejected={rej}' \
                   + ' / Remaining={remain} ({remain_pct:.0f}%) / Orig={orig}').format(
                       cur=self.main_index,
                       acc=num_accepted, rej=num_rejected,
                       acc_pct = frac_accepted,
                       remain=num_remaining, remain_pct=frac_remaining,
                       orig=num_orig)
        stdscr.addstr(1, 1, message)
        if len(self.main) > 0:
            image_message = self.main[self.main_index]
        else:
            image_message = ''            
        stdscr.addstr(2, 1, image_message)
        stdscr.addstr(3, 1, self.status)

        #stdscr.addstr(5, 1, str(self.main))
        #stdscr.addstr(6, 1, str(self.accepted))
        #stdscr.addstr(7, 1, str(self.rejected))

    def next_image(self, stdscr):
        """Display the next image.

        Make no changes in classification.
        """
        self.main_index += 1
        if self.main_index >= len(self.main):
            self.main_index = len(self.main) - 1
        self.update_display(stdscr)

    def goto_image(self, stdscr):
        """Display image N.

        Make no changes in classification, only advance the index pointer."""
        num_string = ''
        char = ''
        while char != '\n':
            char = stdscr.getkey()
            num_string += char
        if len(num_string) > 0:
            try:
                self.main_index = int(num_string)
            except ValueError:
                return
        if self.main_index >= len(self.main):
            self.main_index = len(self.main) - 1
        if self.main_index <= 0:
            self.main_index = 0
        self.update_display(stdscr)

    def previous_image(self, stdscr):
        """Display the previous image.

        Make no changes in classification.
        """
        self.main_index -= 1
        if self.main_index <= 0:
            self.main_index = 0
        self.update_display(stdscr)
        

    def accept_image(self, stdscr):
        """Accept the current image.

        Display the next unclassified image.
        """
        accepted_image = self.main[self.main_index]
        self.main = self.main[:self.main_index] + \
            self.main[self.main_index + 1:]
        self.accepted += [accepted_image]
        self.update_display(stdscr)
        

    def reject_image(self, stdscr):
        """Reject the current image.

        Display the next unclassified image.
        """
        rejected_image = self.main[self.main_index]
        self.main = self.main[:self.main_index] + \
            self.main[self.main_index + 1:]
        self.rejected += [rejected_image]
        self.update_display(stdscr)
        

    def rep_loop(self, stdscr):
        """Read-Eval-Print loop."""
        while len(self.main) > 0:
            self.status = ''
            char = stdscr.getkey()
            if 'q' == char:
                self.write()
                return
            try:
                {'n': self.next_image,
                 'g': self.goto_image,
                 'p': self.previous_image,
                 'a': self.accept_image,
                 'r': self.reject_image,
                 'w': lambda s: self.write(),
                 '\n': self.next_image,
                 }[char](stdscr)
            except KeyError:
                self.status = 'Key Error'
            self.update_status(stdscr)
        self.write()
        return

def main():
    """Do what we do."""
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    images = ImageFiles()

if __name__ == "__main__":
    main()
