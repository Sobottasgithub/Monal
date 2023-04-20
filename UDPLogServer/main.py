#!/usr/bin/python3

#MONAL LOG VIEWER (MLV)

import sys
import json
import struct
import os
from PyQt5 import QtWidgets, uic, QtGui
from internals.interpreter import run

entrys = []
filter_list = []
path_to_file = ""

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uifile = os.path.join(os.path.dirname(sys.argv[0]), "user_interface.ui")
        uic.loadUi(uifile, self)
        self.setWindowTitle("MONAL LOG VIEWER")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(sys.argv[0]), "monal_udp_viewer.png")))
                                  
        #buttons and checkboxes
        self.open_file_browser.clicked.connect(self.open_file)
        self.search_input_submit.clicked.connect(self.search_input_submit_)
        self.settings_button.clicked.connect(self.settings_submit_)
        #self.code_input_submit.clicked.connect(self.code_input_submit_)

        #text-input
        self.search_input = self.findChild(QtWidgets.QLineEdit, 'search_input')
        self.code_input = self.findChild(QtWidgets.QLineEdit, 'code_input')

    def calcColor(self, flag):
        if int(flag) == 1: #error
            return (QtGui.QColor(255, 111, 102), QtGui.QColor(0, 0, 0)) # red | black
        elif int(flag) == 2: #warning
            return (QtGui.QColor(254,134,0), QtGui.QColor(0, 0, 0)) # orange | black
        elif int(flag) == 4: #info
            return (QtGui.QColor(0,214,0), None) # green | white
        elif int(flag) == 8: #debug
            return (QtGui.QColor(1,175,255), None) # blue | white
        elif int (flag) == 16: #verbose
            return (QtGui.QColor(148, 149, 149), None) # grey | white

    #This function filters all entrys that are written in the listview
    def filter_color_and_display(self, entry_i):
        global entrys
        global filter_list
        global path_to_file

        self.finished_message = entry_i['formattedMessage']

        fg, bg = self.calcColor(entry_i['flag'])
        item_with_color = QtWidgets.QListWidgetItem(self.finished_message)
        item_with_color.setForeground(fg)
        if bg != None:
            item_with_color.setBackground(bg)
        self.loglist.addItem(item_with_color)

    #this function is triggerd if a new file is opened.
    def open_file(self):
        global entrys
        global filter_list
        global path_to_file

        self.loglist.clear()
        filter_list = []

        # Open file Browser
        file , check = QtWidgets.QFileDialog.getOpenFileName(None, "Choose a Logfile",
                            "", "Raw Log (*.rawlog)")
        
        if check:
            path_to_file = str(file)

            fp = open(path_to_file, "rb") # open log

            while True:
                #Unpacks the rawlog file and strips down the values
                acht_bytes = fp.read(8)
                if len(acht_bytes) != 8:
                    break

                jason_read_len = struct.unpack("!Q", acht_bytes)
                jason_read_len = jason_read_len[0]
                block_output = fp.read(jason_read_len)
                if len(block_output) != jason_read_len:
                    raise Exception("File Corupt")

                decoded = json.loads(str(block_output, "UTF-8"))
                entrys.append(decoded)

            for i in range(len(entrys)):
                self.entry_i = entrys[i]
                self.filter_color_and_display(self.entry_i)

    # this function is used to show every entry with that search word contained
    def search_input_submit_(self):
        global entrys
        global filter_list
        global path_to_file

        self.lower_or_uppercase = self.lower_uper_case_switch.isChecked()
    
        self.check_list = []

        self.loglist.clear()
        self.search_string = str(self.search_input.text())

        if self.lower_or_uppercase == True: # everything in lowercase
            self.search_string = self.search_string.lower()

            if entrys != None and entrys != []:
                if self.search_string != None:
                    for i in range(len(entrys)):
                        self.entry_index = entrys[i]
                        self.containing_message = self.entry_index['formattedMessage']
                        self.containing_message = self.containing_message.lower()

                        if self.search_string in self.containing_message:
                                self.filter_color_and_display(self.entry_index)
                                self.check_list.append(" ")
                        else:
                            pass
                    if len(self.check_list) <= 0:
                        self.item_with_color =  QtWidgets.QListWidgetItem('Theres NO entry that contains "'+ str(self.search_string) +'"!')
                        self.item_with_color.setForeground(QtGui.QColor(0,0,0)) #grey
                        self.loglist.addItem(self.item_with_color)

                        # filter_list.append(self.finished_message)
                    else:
                        pass
                else:
                    pass
            else: 
                self.item_with_color =  QtWidgets.QListWidgetItem("PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(QtGui.QColor(255,111,102)) #grey
                self.loglist.addItem(self.item_with_color)

        elif self.lower_or_uppercase == False: # everything like it used to be
            if entrys != None and entrys != []:
                if self.search_string != None:
                    for i in range(len(entrys)):
                        self.entry_index = entrys[i]
                        self.containing_message = self.entry_index['formattedMessage']

                        if self.search_string in self.containing_message:
                                self.filter_color_and_display(self.entry_index)
                                self.check_list.append(" ")
                        else:
                            pass
                    if len(self.check_list) <= 0:
                        self.item_with_color =  QtWidgets.QListWidgetItem('Theres NO entry that contains"'+ str(self.search_string) +'"!')
                        self.item_with_color.setForeground(QtGui.QColor(233,233,233)) #grey
                        self.loglist.addItem(self.item_with_color)
                    else:
                        pass
                else:
                    pass
            else: 
                self.item_with_color =  QtWidgets.QListWidgetItem("PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(QtGui.QColor(255,111,102)) #red
                self.loglist.addItem(self.item_with_color)
        else: 
            pass # ERROR

    #this function is for controling color etc
    def settings_submit_(self):
        pass #not included

    # this function is used to process your code :)
    def code_input_submit_(self):
        global entrys
        global filter_list
        global path_to_file

        '''
        if len(sys.argv) != 2:
            print("Usage: %s <fileToRun>" % "@print('hello world');")
           sys.exit(1)
        '''

        self.code_input_ = str(self.code_input.text())
        
        if len(self.code_input_) <= 0:
            print("Something went Wrong!")
        elif len(self.code_input_) >= 1:
            run(self.code_input_)



app = QtWidgets.QApplication(sys.argv)
window = Ui()
window.show()
app.exec_()
