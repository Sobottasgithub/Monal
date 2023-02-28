#!/usr/bin/python3
import sys
import json
import struct
from PyQt5 import QtWidgets, uic, QtGui
from interpreter import Hello_world

entrys = []
filter_list = []
path_to_file = ""

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("udp 2.0/user_interface.ui", self)
                                  
        #buttons and checkboxes
        self.open_file_browser.clicked.connect(self.open_file)
        self.search_input_submit.clicked.connect(self.search_input_submit_)
        self.code_input_submit.clicked.connect(self.code_input_submit_)

        #text-input
        self.search_input = self.findChild(QtWidgets.QLineEdit, 'search_input')
        self.code_input = self.findChild(QtWidgets.QLineEdit, 'code_input')


    #This function filters all entrys that are written in the listview
    def filter_color_and_display(self, entry_i):
        global entrys
        global filter_list
        global path_to_file

        self.identefyer = entry_i['flag']
        self.finished_message = entry_i['formattedMessage']

        if int(self.identefyer) == 1: # error
            self.item_with_color =  QtWidgets.QListWidgetItem(self.finished_message)
            self.item_with_color.setForeground(QtGui.QColor(255,111,102)) #red
            self.loglist.addItem(self.item_with_color)
            filter_list.append(self.finished_message)

        elif int(self.identefyer) == 2: # warning
            self.item_with_color =  QtWidgets.QListWidgetItem(self.finished_message)
            self.item_with_color.setForeground(QtGui.QColor(254,134,0)) #orange
            self.loglist.addItem(self.item_with_color)
            filter_list.append(self.finished_message)

        elif int(self.identefyer) == 4: # info
            self.item_with_color =  QtWidgets.QListWidgetItem(self.finished_message)
            self.item_with_color.setForeground(QtGui.QColor(0,214,0)) #green
            self.loglist.addItem(self.item_with_color)
            filter_list.append(self.finished_message)

        elif int(self.identefyer) == 8: # debug
            self.item_with_color =  QtWidgets.QListWidgetItem(self.finished_message)
            self.item_with_color.setForeground(QtGui.QColor(1,175,255)) #blue
            self.loglist.addItem(self.item_with_color)
            filter_list.append(self.finished_message)

        elif int(self.identefyer) == 16: # verbose
            self.item_with_color =  QtWidgets.QListWidgetItem(self.finished_message)
            self.item_with_color.setForeground(QtGui.QColor(198,199,198)) #grey
            self.loglist.addItem(self.item_with_color)
            filter_list.append(self.finished_message)

        else:
            pass

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
                        self.item_with_color =  QtWidgets.QListWidgetItem('Theres NO entry that contains "'+ str(self.search_string) +'"!')
                        self.item_with_color.setForeground(QtGui.QColor(0,0,0)) #grey
                        self.loglist.addItem(self.item_with_color)
                    else:
                        pass
                else:
                    pass
            else: 
                self.item_with_color =  QtWidgets.QListWidgetItem("PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(QtGui.QColor(255,111,102)) #grey
                self.loglist.addItem(self.item_with_color)
        else: 
            pass # ERROR

    def code_input_submit_(self):
        
        Hello_world()


app = QtWidgets.QApplication(sys.argv)
window = Ui()
window.show()
app.exec_()