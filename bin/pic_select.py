#!/usr/bin/python


"""A utility to select images.

Known bugs:
  - Probably doesn't handle mouse events
  - Probably handles winch events poorly if at all
  - Probably misses quite a bit of error handling
"""



GPL = """
Copyright 2012  Jeff Abrahamson

This file is part of pic_select.

pic_select is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pic_select is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pic_select.  If not, see <http://www.gnu.org/licenses/>.
"""


import curses
import locale
import subprocess
import sys


#### Copied, then adapted from
#### http://code.activestate.com/recipes/134892/

locale.setlocale(locale.LC_ALL,"")
# code = locale.getpreferredencoding()

def get_ch_gen(scr):
    """Read one character from (probably) stdin using curses."""
    while True:
        char = scr.getch()      # pauses until a key's hit
        scr.nodelay(1)
        backspace = []
        while char != -1:       # check if more data is available
            if char > 255:      # directly yield arrowkeys etc as ints
                yield char
            else:
                backspace.append(chr(char))
                char = scr.getch()
        scr.nodelay(0)
        for char in ''.join(backspace).decode('utf8'):
            yield char


#### End of copy from activestate.com


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


def screen_setup(stdscr):
    """Set up the screen for our curses pleasure."""
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    stdscr.bkgd(' ', curses.color_pair(1))
    curses.curs_set(0)
    #stdscr.clear()
    #stdscr.refresh()


class ImageFiles:
    """Track our decisions thus far, and encapsulate how to behave."""

    main_name = ''
    main = []
    main_index = 0
    accepted = []
    rejected = []
    orig = []
    status = ''
    
    
    def __init__(self):
        """Init, for good measure."""
        pass
    

    def orig_name(self):
        """Return name of file for original image names.

        This is useful to maintain the total order, in case the list
        wasn't alphabetical.
        """
        return self.main_name + '-orig'
    
        
    def accept_name(self):
        """Return name of file for accepted image names."""
        return self.main_name + '-accept'
    
        
    def reject_name(self):
        """Return name of file for rejected image names."""
        return self.main_name + '-reject'
    
        
    def read(self, filename):
        """Read the image list.

        Also check for satellite files that we might have created on a
        previous invocation and set the appropriate data structures if so.
        """
        self.main_name = filename
        self.main = read_file(filename)
        orig = read_file(self.orig_name())
        if [] == orig:
            self.orig = self.main
        else:
            self.orig = orig
        self.accepted = read_file(self.accept_name())
        self.rejected = read_file(self.reject_name())


    def write(self):
        """Write the image files."""

        write_file(self.main_name, self.main)
        write_file(self.accept_name(), self.accepted)
        write_file(self.reject_name(), self.rejected)
        write_file(self.orig_name(), self.orig)


    def update_display(self, stdscr):
        """Update the image and metadata displays."""
        if len(self.main) == 0:
            return;
        if self.main_index >= len(self.main):
            self.main_index =     len(self.main) - 1
        self.update_status(stdscr)
        self.display_image()


    def display_image(self):
        """Display the current image."""
        # geeqie --remote view 
        if self.main_index >= len(self.main):
            return
        subprocess.call(['geeqie', '--remote', 'file:', \
                             self.main[self.main_index]])
        # Pre-cache the next image if it exists. It can take up to two
        # seconds to pull an image from my file server.
        if self.main_index + 1 < len(self.main):
            with open(self.main[self.main_index + 1], 'r') as fp:
                fp.read()
        
    def update_status(self, stdscr):
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
        screen_setup(stdscr)
        self.update_display(stdscr)
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


        
def usage():
    """How to invoke."""

    print sys.argv[0] + " file-of-image-names"
    

def main():
    """Do what we do."""
    if len(sys.argv) == 1:
        usage()
        return
    images = ImageFiles()
    images.read(sys.argv[1])
    curses.wrapper(images.rep_loop)
    

if __name__ == "__main__":
    main()
