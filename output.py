import re

class Output(object):
    def __init__(self, recognizer, lines = None):
        self.lines = []
        self.recognizer = recognizer
        self.observer = None
        if lines is not None:
            for line in lines:
                self.appendLine(line)        

    def appendLine(self, line):
        level = self.recognizer.recognize(line)
        #print "line with level %s" % str(level) 
        self.lines.append((line, level, len(self.lines)))
        if self.observer is not None:
            self.observer.onLineAdded(line, level)
        return level

    def get(self, levels, regexes = None, returnOriginalLineIndices=False):
        
        if regexes is None:
            regexes = []
        regexes = map(re.compile, regexes)
        
        def match(line):
            ret = False
            if line[1] in levels:
                ret = True
                for regex in regexes:
                    if not regex.search(line[0]):
                        ret = False
                        break
            return ret
            
        lines = filter(match, self.lines)
        print "%d of %d lines match" % (len(lines), len(self.lines))
        lineIndices = None
        if returnOriginalLineIndices:
            lineIndices = map(lambda x: x[2], lines)
        lines = map(lambda x: x[0], lines)
        filteredText = "".join(lines)
        if returnOriginalLineIndices:
            return (filteredText, lineIndices)
        else:
            return filteredText
    
    def clear(self):
        self.lines = []
    
    def setObserver(self, observer):
        self.observer = observer

class OutputLevelSettings(object):

    def __init__(self, levels, recognizerFactory):
        self.levels = levels
        self.recognizerFactory = recognizerFactory

    def recognizer(self):
        self.recognizerFactory()

class StandardJavaOutputLevelSettings(OutputLevelSettings):
	class LevelRecognizer(object):
		def __init__(self):
			self.prevLevel = None
		
		def recognize(self, line):
			level = 0
			if line.startswith("INFO"): level = 1
			if line.startswith("DEBUG"): level = 2
			if line.startswith("ERROR"): level = 3
			if line.startswith("WARN"): level = 4
			if line.startswith("TRACE"): level = 5
			return level

	def __init__(self):
		OutputLevelSettings.__init__(self, {0:'unknown', 1:'info', 2:'debug', 3:'error', 4:'warning', 5:'trace'}, StandardJavaOutputLevelSettings.LevelRecognizer)
