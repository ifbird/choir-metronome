# import midiutil
# from midiutil.MidiFile import MIDIFile

from time import sleep

import os
import sys
import re

import parameter as p

from PySide import QtGui
import midiclass
from PySide import QtGui

class Example(QtGui.QMainWindow):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.convert_to_midi)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        btn_play = QtGui.QPushButton("Play", self)
        btn_play.move(30, 50)

        btn_play.clicked.connect(self.play_midi_file)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('MIDI conversion')
        self.show()

    def convert_to_midi(self):
      try:
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open numbered notation file', '/home')

        with open(fname, 'r') as f:
          # data = f.read()
          # self.textEdit.setText(data)
          self.midi_file_name = os.path.splitext(fname)[0] + '.mid'
          mw = midiclass.MidiWorld(fname)
          mw.write_midifile(self.midi_file_name)
      except:
        pass

    def play_midi_file(self):
      try:
        midiclass.play_midi(self.midi_file_name)
      except:
        pass

def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
