# simpleUI widgets module
#
# (C) 2006-2013 by Dominik Jain
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from text import SyntaxHighlightingText, ScrolledText2
from filePick import FilePick, FilePickEdit
import Tkinter

try:
    import Pmw
    havePMW = True
except:
    havePMW = False

class DropdownList:
    def __init__(self, master, items, default=None, allowNone=False, onSelChange=None):
        self.allowNone = allowNone
        self.master = master
        self.onSelChange = onSelChange
        self.gridded = False
        self.setItems(items)
        if default is not None:
            self.set(default)
        else:
            self.set(self.items[0])

    def __getattr__(self, name):
        return getattr(self.list, name)

    def get(self):
        return self.picked_name.get()

    def set(self, item):
        if item in self.items:
            if not havePMW:
                self.picked_name.set(item)
            else:
                self.list.selectitem(item)
                #self.onSelChange(default_file)

    def grid(self, **args):
        self.gridded = True
        self.gridArgs = args
        self.list.grid(**args)

    def setItems(self, items):
        if self.gridded:
            self.list.grid_forget()
        if self.allowNone:
            items = tuple([""] + list(items))
        self.items = items
        if havePMW:
            self.list = Pmw.ComboBox(self.master, selectioncommand = self.onSelChange, scrolledlist_items = items)
            self.list.component('entryfield').component('entry').configure(state = 'readonly', relief = 'raised')
            self.picked_name = self.list
        else:
            self.picked_name = Tkinter.StringVar(self.master)
            self.list = apply(Tkinter.OptionMenu, (self.master, self.picked_name) + tuple(items))
            if self.onSelChange is not None:
                self.picked_name.trace("w", self.onSelChange)
        if self.gridded:
            self.list.grid(**self.gridArgs)


class Checkbox(Tkinter.Checkbutton):
    def __init__(self, master, text, default=None, **args):
        self.var = IntVar()
        Checkbutton.__init__(self, master, text=text, variable=self.var, **args)
        if default is not None:
            self.var.set(default)

    def get(self):
        return self.var.get()
