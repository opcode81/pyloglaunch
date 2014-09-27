#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from Tkinter import *
import os
import pickle
from output import Output
from simpleui import ScrolledText2

# --- main gui class ---

class LogViewerUI(object):

    def __init__(self, master, debugLevelSettings, lines = None):
        self.dls = debugLevelSettings

        master.title("LogViewer")
        
        # read previously saved settings
        settings = {}
        self.configname = "logViewer.cfg"
        if os.path.exists(self.configname):
            try:
                settings = pickle.loads("\n".join(map(lambda x: x.strip("\r\n"), file(self.configname, "r").readlines())))
            except:
                pass

        self.settings = settings

        self.master = master
        self.currentProcessName = None
        self.currentProcess = None
        
        self.frame = Frame(master)
        self.frame.pack(fill=BOTH, expand=1)
        self.frame.columnconfigure(1, weight=1)

        if lines is None: lines = []
        print "%d lines" % len(lines)
        
        self.logViewer = LogViewer(self.frame, self.master, debugLevelSettings, selectedOutputLevels=self.settings.get("outputLevels"), delegate=self, initialOutputLines=lines, useClipboardButton=True)
        
        self.setGeometry()

    def setGeometry(self):
        g = self.settings.get("geometry")
        if g is None: return
        self.master.geometry(g)
        
    def saveSettings(self):
        self.settings["geometry"] = self.master.winfo_geometry()
        self.settings["outputLevels"] = self.logViewer.outputLevels
        pickle.dump(self.settings, file(self.configname, "w+"))
    
    # LogViewer delegate
    
    def onChangeOutputLevel(self):
        self.saveSettings()


class LogViewer(object):
    def __init__(self, frame, master, debugLevelSettings, initialOutput=None, initialOutputLines=None, selectedOutputLevels=None, delegate=None, instantSearch=False, useClipboardButton=False):
        self.master = master
        self.dls = debugLevelSettings
        self.frame = frame
        self.instantSearch = instantSearch
        self.delegate = delegate
        self.frame.columnconfigure(1, weight=1)
        
        row = -1
        
        row += 1    
        optFrame = Frame(self.frame)
        
        # log levels/options
        self.cbOutputLevel = {}
        if selectedOutputLevels is None: selectedOutputLevels = set([key for key in self.dls.levels])
        self.outputLevels = selectedOutputLevels
        for id, name in self.dls.levels.iteritems():
            var = IntVar()
            cb = Checkbutton(optFrame, text=name, variable=var, command=self.onChangeOutputLevel)
            cb.pack(side=LEFT)
            var.set(1 if id in self.outputLevels else 0)
            self.cbOutputLevel[id] = var
        if useClipboardButton:
            button = Button(optFrame, text="use clipboard text as log", command=self.useClipboardText)
            button.pack(side=LEFT)
        button = Button(optFrame, text="clear log", command=self.clearLog)
        button.pack(side=LEFT)
        optFrame.grid(row=row, column=1, sticky="NEWS")

        # output text field
        row += 1
        self.output = ScrolledText2(self.frame)
        #self.output = ScrolledText(self.frame,wrap=NONE,bd=0,width=80,height=25,undo=1,maxundo=50,padx=0,pady=0,background="white",foreground="black")
        self.output.grid(row=row,column=1, sticky="NWES")
        self.frame.rowconfigure(row, weight=1)
        
        self.output.tag_config("hl", background="yellow")

        # regex
        row += 1
        searchFrame = Frame(self.frame)
        self.regex = StringVar()
        self.regex.trace("w", self.onChangeRegEx)
        e = Entry(searchFrame, textvariable=self.regex)
        e.pack(side=LEFT, fill=BOTH, expand=1)
        if not self.instantSearch:
            btn = Button(searchFrame, text="search", command=self.searchRegEx)
            btn.pack(side=LEFT)
        btn = Button(searchFrame, text="locate", command=self.locateFilteredLine)
        btn.pack(side=LEFT)
        searchFrame.grid(row=row, column=1, sticky="NEWS")
        
        # filtered text field
        row += 1
        self.filteredOutput = ScrolledText2(self.frame)
        self.filteredOutput.grid(row=row, column=1, sticky="NEWS")
        self.frame.rowconfigure(row, weight=1)

        if initialOutputLines is not None: self.setLogLines(initialOutputLines)
        elif initialOutput is not None: self.setLog(initialOutput)
    
    def setLogLines(self, lines):
        self.setLog(Output(self.dls.recognizerFactory(), lines))
    
    def setLog(self, log):
        self.log = log
        log.setObserver(self)
        self.setOutput(self.getFilteredText(onlyLevel=True))        
        
    def setOutput(self, output):
        #self.output.config(state=NORMAL)
        self.output.delete("1.0", END)
        self.output.insert(INSERT, output)
        self.output.see(END)
        #self.output.config(state=DISABLED)

    def setFilteredOutput(self, output):
        self.filteredOutput.delete("1.0", END)
        self.filteredOutput.insert(INSERT, output)
        self.filteredOutput.see(END)
    
    def appendOutput(self, output, level):
        if level in self.outputLevels:
            self.output.insert(END, output)
            
    def getFilteredText(self, onlyLevel=False):
        ''' onlyLevel: if True, only filter by level, otherwise also consider current regex '''
        regex = self.regex.get().strip()
        regexes = [] if regex == "" or onlyLevel else [regex]
        text, lineIndices = self.log.get(self.outputLevels, regexes, returnOriginalLineIndices=True)
        self.filteredLineIndices = lineIndices
        #print "Text:\n", text
        return text
    
    def locateFilteredLine(self):
        line = map(int, self.filteredOutput.index(INSERT).split("."))[0]
        line = line - 1
        originalIndex = self.filteredLineIndices[line]
        print "original index:", originalIndex
        pos1 = "%d.0" % (originalIndex+1)
        self.output.see(pos1)  
        self.output.tag_add("hl", pos1, "%d.end" % (originalIndex+1)) # TODO FIXME: only works if all log levels are enabled      

    def onChangeOutputLevel(self):
        for key, cb in self.cbOutputLevel.iteritems():
            if int(cb.get()):
                self.outputLevels.add(key)
            elif key in self.outputLevels:
                self.outputLevels.remove(key)
        self.setOutput(self.getFilteredText(onlyLevel=True))
        if self.delegate is not None:
            self.delegate.onChangeOutputLevel()
    
    def onChangeRegEx(self, *args):
        if self.instantSearch:
            self.searchRegEx()

    def searchRegEx(self, *args):
        self.setFilteredOutput(self.getFilteredText(onlyLevel=False))
    
    def useClipboardText(self, *args):
        cltext = self.master.clipboard_get()
        self.setLogLines(map(lambda l: l + "\n", cltext.split("\n")))
        self.updateOutput()
    
    def updateOutput(self):
        self.setOutput(self.getFilteredText(onlyLevel=True))
    
    def clearLog(self):
        self.log.clear()
        self.updateOutput()

    # Output delegate
    
    def onLineAdded(self, line, level):
        self.appendOutput(line, level)

		
# -- main app: example --

if __name__ == '__main__':    
    from output import StandardJavaOutputLevelSettings	

    # create gui
    root = Tk()
    app = LogViewerUI(root, StandardJavaOutputLevelSettings())
    root.mainloop()

