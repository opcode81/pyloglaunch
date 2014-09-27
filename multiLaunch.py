#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

from Tkinter import *
import os
import pickle
import subprocess
from Queue import Queue
from threading import Thread
import time
from output import Output
from simpleui import ScrolledText2
from logViewer import LogViewer

class MLProcess(object):
    def __init__(self, name, command, printOutput=True):
        self.name = name
        self.command = command
        self.queue = Queue()
        self.printOutput = printOutput

    def start(self):
        print "starting %s" % self.command
        self.p = subprocess.Popen(self.command, shell=True, bufsize=1024*1024, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False)
        self.stdin = self.p.stdin
        self.stdout = self.p.stdout
        self.stderr = self.p.stderr
    
    def _enqueueOutput(self,stream):
        for line in iter(stream.readline, b''):
            if self.printOutput: print "%s: %s" % (self.name, line), 
            self.queue.put(line)

    def startOutputThread(self):
        Thread(target=lambda stream=self.stdout: self._enqueueOutput(stream)).start()
        Thread(target=lambda stream=self.stderr: self._enqueueOutput(stream)).start()
    
    def readlines(self):
        i = 0;
        l = []
        while i < 100:
            line = self.stdout.readline()
            if line is None: 
                break
            #print "%s: %s" % (self.name, line),
            l.append(line)
            i += 1
        print l
        return l

    def isRunning(self):
        return self.p.returncode is None

    def __str__(self):
        return "MLProcess[%s]" % self.name

class MultiLaunch(object):
    def __init__(self, *processes):
        self.processes = processes
        
    def launch(self):
        for p in self.processes:
            p.start()
    
    def join(self, printOutput = True):
        ''' waits for all processes to be terminated, printing their output if requested '''
        if printOutput:
            for p in self.processes:
                p.startOutputThread()
        isRunning = True
        while isRunning:
            isRunning = False
            for p in self.processes:
                if printOutput:
                    while not p.queue.empty():
                        print "%s: %s" (p.name, p.queue.get()), 
                if p.isRunning():
                    isRunning = True
            time.sleep(2)
            

# --- main gui class ---

class MultiLaunchUI(object):

    def __init__(self, master, multiLaunch, debugLevelSettings):
        self.dls = debugLevelSettings

        master.title("MultiLaunch")
        
        # read previously saved settings
        settings = {}
        self.configname = "multiLaunch.cfg"
        if os.path.exists(self.configname):
            try:
                settings = pickle.loads("\n".join(map(lambda x: x.strip("\r\n"), file(self.configname, "r").readlines())))
            except:
                pass

        self.settings = settings

        self.master = master
        self.multiLaunch = multiLaunch
        self.currentProcessName = None
        self.currentProcess = None
        
        self.frame = Frame(master)
        self.frame.pack(fill=BOTH, expand=1)
        self.frame.columnconfigure(0, weight=1)

        row = -1

        # processes
        row += 1
        buttonFrame = Frame(self.frame)
        self.procByName = {}
        for p in self.multiLaunch.processes:
            name = p.name
            self.procByName[name] = p
            p.output = Output(self.dls.recognizerFactory())
            button = Button(buttonFrame, text=name, command=lambda name=name: self.onSelectProcess(name))
            button.pack(side=LEFT)
        buttonFrame.grid(row=row, column=0, sticky="NEWS")

        row += 1
        viewerFrame = Frame(self.frame)
        self.logViewer = LogViewer(viewerFrame, self.master, self.dls, selectedOutputLevels=self.settings.get("outputLevels"), delegate=self, initialOutputLines=[])
        viewerFrame.grid(row=row, column=0, sticky="NEWS")

        self.setGeometry()
        
        self.multiLaunch.launch()
        print "launched all processes"
        
        # start threads
        for p in self.multiLaunch.processes:
            p.startOutputThread()
        
        print "starting queue updates"
        self.updateFromQueues()
    
    def onSelectProcess(self, name):
        print "selected %s" % name
        self.currentProcessName = name
        p = self.procByName[name]
        self.currentProcess = p
        self.logViewer.setLog(p.output)
        self.saveSettings()
        
    def setGeometry(self):
        g = self.settings.get("geometry")
        if g is None: return
        self.master.geometry(g)
        
    def saveSettings(self):
        self.settings["geometry"] = self.master.winfo_geometry()
        self.settings["outputLevels"] = self.logViewer.outputLevels
        pickle.dump(self.settings, file(self.configname, "w+"))

    def updateFromQueues(self):
        for p in self.multiLaunch.processes:
            while not p.queue.empty():
                line = p.queue.get()
                #print "got line: %s" %line,
                level = p.output.appendLine(line)
                #if p.name == self.currentProcessName:
                #    self.appendOutput(line, level)
        self.master.after(500, self.updateFromQueues)

    # LogViewer delegate
        
    def onChangeOutputLevel(self):
        self.saveSettings()


class DebugLevelSettings(object):

    def __init__(self, levels, recognizerFactory):
        self.levels = levels
        self.recognizerFactory = recognizerFactory

    def recognizer(self):
        self.recognizerFactory()

# -- main app: example --

if __name__ == '__main__':    
    from output import StandardJavaOutputLevelSettings	
    
    processes = []
    processes.append(MLProcess("ls", "ls"))
    processes.append(MLProcess("ls -a", "ls -a"))
    ml = MultiLaunch(*processes)

    # create gui
    root = Tk()
    app = MultiLaunchUI(root, ml, StandardJavaOutputLevelSettings())
    root.mainloop()

