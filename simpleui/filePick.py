# simpleUI file picker widgets
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

from Tkinter import *
try:
    import Pmw
    havePMW = True
except:
    havePMW = False
import os
from fnmatch import fnmatch
from text import SyntaxHighlightingText, ScrolledText2

class FilePickEdit(Frame):
    def reloadFile(self):
        self.editor.delete("1.0", END)
        filename = self.picked_name.get()
        if os.path.exists(filename):
            new_text = file(filename).read()
            if new_text.strip() == "":
                new_text = "// %s is empty\n" % filename;
            new_text = new_text.replace("\r", "")
        else:
            new_text = ""
        self.editor.insert(INSERT, new_text)

    def onSelChange(self, name, index=0, mode=0):
        self.reloadFile()
        filename = self.picked_name.get()
        self.save_name.set(filename)
        self.save_edit.configure(state=DISABLED)
        self.unmodified = True
        if self.user_onChange != None:
            self.user_onChange(filename)

    def onSaveChange(self, name, index, mode):
        if self.user_onChange != None:
            self.user_onChange(self.save_name.get())

    def autoRename(self):
        # modify "save as" name
        filename = self.picked_name.get()
        if filename == "": filename = "new" + self.file_extension # if no file selected, create new filename
        ext = ""
        extpos = filename.rfind(".")
        if extpos != -1: ext = filename[extpos:]
        base = filename[:extpos]
        hpos = base.rfind("-")
        num = 0
        if hpos != -1:
            try:
                num = int(base[hpos+1:])
                base = base[:hpos]
            except:
                pass
        while True:
            num += 1
            filename = "%s-%d%s" % (base, num, ext)
            if not os.path.exists(filename):
                break
        self.save_name.set(filename)
        # user callback
        if self.user_onChange != None:
            self.user_onChange(filename)

    def onEdit(self):
        if self.unmodified == True:
            self.unmodified = False
            # do auto rename if it's enabled or there is no file selected (editing new file)
            if self.rename_on_edit.get() == 1 or self.picked_name.get() == "":
                self.autoRename()
            # enable editing of save as name
            self.save_edit.configure(state=NORMAL)

    def onChangeRename(self):
        # called when clicking on "rename on edit" checkbox
        if self.rename_on_edit.get() == 1:
            if (not self.unmodified) and self.save_name.get() == self.picked_name.get():
                self.autoRename()
        else:
            self.save_name.set(self.picked_name.get())

    def __init__(self, master, file_mask, default_file, edit_height = None, user_onChange = None, rename_on_edit=0, font = None, coloring=True, allowNone=False, highlighter=None):
        '''
            file_mask: file mask (e.g. "*.foo") or list of file masks (e.g. ["*.foo", "*.abl"])
        '''
        self.master = master
        self.user_onChange = user_onChange
        Frame.__init__(self, master)
        row = 0
        self.unmodified = True
        self.allowNone = allowNone
        self.file_extension = ""
        if type(file_mask) != list:
            file_mask = [file_mask]
        if "." in file_mask[0]:
            self.file_extension = file_mask[0][file_mask[0].rfind('.'):]
        # read filenames
        self.file_mask = file_mask
        self.updateList()
        # filename frame
        self.list_frame = Frame(self)
        self.list_frame.grid(row=row, column=0, sticky="WE")
        self.list_frame.columnconfigure(0, weight=1)
        # create list
        self.picked_name = StringVar(self)
        self.makelist()
        # save button
        self.save_button = Button(self.list_frame, text="save", command=self.save, height=1)
        self.save_button.grid(row=0, column=1, sticky="E")
        # editor
        row += 1
        if coloring:
            self.editor = SyntaxHighlightingText(self, self.onEdit, highlighter=highlighter)
        else:
            self.editor = ScrolledText2(self, self.onEdit)
        if font != None:
            self.editor.configure(font=font)
        if edit_height is not None:
            self.editor.configure(height=edit_height)
        self.editor.grid(row=row, column=0, sticky="NEWS")
        self.rowconfigure(row, weight=1)
        self.columnconfigure(0, weight=1)
        # option to change filename on edit
        row += 1
        self.options_frame = Frame(self)
        self.options_frame.grid(row=row, column=0, sticky=W)
        self.rename_on_edit = IntVar()
        cb = Checkbutton(self.options_frame, text="rename on edit", variable=self.rename_on_edit)
        cb.pack(side=LEFT)
        cb.configure(command=self.onChangeRename)
        self.rename_on_edit.set(rename_on_edit)
        # filename frame
        row += 1
        self.filename_frame = Frame(self)
        self.filename_frame.grid(row=row, column=0, sticky="WE")
        self.filename_frame.columnconfigure(0, weight=1)
        # save as filename
        self.save_name = StringVar(self)
        self.save_edit = Entry(self.filename_frame, textvariable = self.save_name)
        self.save_edit.grid(row=0, column=0, sticky="WE")
        self.save_name.trace("w", self.onSaveChange)
        # pick default if applicable
        self.select(default_file)
        self.row = row

    def updateList(self):
        self.files = []
        if self.allowNone:
            self.files.append("")
        for filename in os.listdir("."):
            for fm in self.file_mask:
                if fnmatch(filename, fm):
                    self.files.append(filename)
        self.files.sort()
        if len(self.files) == 0 and not self.allowNone: self.files.append("(no %s files found)" % str(self.file_mask    ))

    def select(self, filename):
        ''' selects the item given by filename '''
        if filename in self.files:
            if not havePMW:
                self.picked_name.set(filename)
            else:
                self.list.selectitem(self.files.index(filename))
                self.onSelChange(filename)

    def makelist(self):
        if havePMW:
            self.list = Pmw.ComboBox(self.list_frame,
                    selectioncommand = self.onSelChange,
                    scrolledlist_items = self.files,
            )
            self.list.grid(row=0, column=0, padx=0, pady=0, sticky="NEWS")
            self.list.component('entryfield').component('entry').configure(state = 'readonly', relief = 'raised')
            self.picked_name = self.list
        else:
            self.list = apply(OptionMenu, (self.list_frame, self.picked_name) + tuple(self.files))
            self.list.grid(row=0, column=0, sticky="NEW")
            self.picked_name.trace("w", self.onSelChange)

    def save(self):
        self.get()

    def set(self, selected_item):
        self.select(selected_item)

    def get(self):
        ''' gets the name of the currently selected file, saving it first if necessary '''
        filename = self.save_name.get()
        if self.unmodified == False:
            self.unmodified = True
            # save the file
            f = file(filename, "w")
            f.write(self.editor.get("1.0", END))
            f.close()
            # add it to the list of files
            if not filename in self.files:
                self.files.append(filename)
                self.files.sort()
                self.list.destroy()
                self.makelist()
            # set it as the new pick
            #if havePMW:
            #    self.picked_name.selectitem(self.files.index(filename), 1)
            #else:
            #    self.picked_name.set(filename)
            self.select(filename)
            self.save_edit.configure(state=DISABLED)
        return filename

    def get_text(self):
        return self.editor.get("1.0", END)

    def get_filename(self):
        return self.save_name.get()


class FilePick(Frame):
    def __init__(self, master, file_mask, default_file, user_onChange = None, font = None, dirs = (".", ), allowNone = False):
        ''' file_mask: file mask or list of file masks '''
        self.master = master
        self.user_onChange = user_onChange
        Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.unmodified = True
        self.file_extension = ""
        if "." in file_mask:
            self.file_extension = file_mask[file_mask.rfind('.'):]
        if type(file_mask) != list:
            file_mask = [file_mask]
        self.file_masks = file_mask
        self.allowNone = allowNone
        self.dirs = dirs
        # create list of files
        self.updateList()
        # pick default if applicable
        self.set(default_file)

    def onSelChange(self, name, index=0, mode=0):
        filename = self.picked_name.get()
        if self.user_onChange != None:
            self.user_onChange(filename)

    def updateList(self):
        prev_sel = self.get()
        # get list of files (paths)
        self.files = []
        if self.allowNone:
            self.files.append("")
        for fm in self.file_masks:
            for dir in self.dirs:
                try:
                    for filename in os.listdir(dir):
                        if fnmatch(filename, fm):
                            if dir != ".":
                                path = os.path.join(dir, filename)
                            else:
                                path = filename
                            self.files.append(path)
                except:
                    pass
        self.files.sort()
        if len(self.files) == 0: self.files.append("(no %s files found)" %  self.file_masks)
        # create list object
        self._makelist()
        # reselect
        self.set(prev_sel)

    def getList(self):
        ''' returns the current list of files '''
        return self.files

    def _makelist(self):
        if havePMW:
            self.list = Pmw.ComboBox(self,
                    selectioncommand = self.onSelChange,
                    scrolledlist_items = self.files,
            )
            self.list.grid(row=0, column=0, padx=0, sticky="NEWS")
            self.list.component('entryfield').component('entry').configure(state = 'readonly', relief = 'raised')
            self.picked_name = self.list
        else:
            self.picked_name = StringVar(self)
            self.list = apply(OptionMenu, (self, self.picked_name) + tuple(self.files))
            self.list.grid(row=0, column=0, sticky="NEW")
            self.picked_name.trace("w", self.onSelChange)

    def set(self, filename):
        default_file = filename
        if default_file in self.files:
            if not havePMW:
                self.picked_name.set(default_file) # default value
            else:
                self.list.selectitem(self.files.index(default_file))
                self.onSelChange(default_file)
                pass

    def get(self):
        if not hasattr(self, 'picked_name'):
            return None
        return self.picked_name.get()
