#!/usr/bin/python3

# MONAL LOG VIEWER (MLV)

import sys
import json
import struct
import os
from PyQt5 import QtWidgets, uic, QtGui
from internals.interpreter import run

#global values
entries = []
filter_list = []
path_to_file = ""
num_of_settings_window_create = 1
settings_window_create = None  # (settings_submit_)
color_json_read = None  # (setting all colors)

# class to make the ui and all functions!
class Main_Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        global color_json_read

        self.setFixedSize(1400, 840)

        uic.loadUi(os.path.join(os.path.dirname(
            sys.argv[0]), "ui_files/user_interface.ui"), self)
        self.setWindowTitle("MLV | Monal Log Viewer")
        self.setWindowIcon(QtGui.QIcon(os.path.join(
            os.path.dirname(sys.argv[0]), "monal_log_viewer.png")))

        self.color_json_refresh()

        #buttons and checkboxes
        self.open_file_browser.clicked.connect(self.open_file)
        self.search_input_submit.clicked.connect(self.search_input_submit_)
        self.settings_button.clicked.connect(self.settings_submit_)
        self.code_input_submit.clicked.connect(self.code_input_submit_)

        self.use_preset_query_drp.currentIndexChanged.connect(self.preset_query_submit) # not finished WORK IN PROGRESS

        # text-input
        self.search_input = self.findChild(QtWidgets.QLineEdit, 'search_input')
        self.code_input = self.findChild(QtWidgets.QLineEdit, 'code_input')

    # this codeblock is used to get the colors
    def color_json_refresh(self):
        global color_json_read

        self.color_json_read_ = open(os.path.join(
            os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "rb")
        self.color_json_read_ = self.color_json_read_.read()
        self.color_json_read_ = json.loads(str(self.color_json_read_, "UTF-8"))
        color_json_read = self.color_json_read_

        # list background
        self.color_json_read_ = color_json_read['background-color']
        self.loglist.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
            self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); border: 0px solid black;")
        self.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
            self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #efefef;")

        # nav background
        self.color_json_read_ = color_json_read['nav-background-color']
        if self.color_json_read_ >= [127, 127, 127]:
            self.widget_2.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
                self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #000;")
        else:
            self.widget_2.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
                self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #efefef;")
            
        self.use_preset_query_drp.clear()
        self.preset_query_list_app = color_json_read['preset_querys']
        self.use_preset_query_drp.addItem("Choose a query...")
        for i in self.preset_query_list_app:
            self.use_preset_query_drp.addItem(i)

    # a function to give the entrys color
    def calcColor(self, flag):
        global color_json_read
        if int(flag) == 1:  # ERROR
            self.color_json_read_ = color_json_read['error-color'] # red | black
            return (QtGui.QColor(self.color_json_read_[0], self.color_json_read_[1], self.color_json_read_[2]), QtGui.QColor(0, 0, 0))
        elif int(flag) == 2:  # WARNING
            self.color_json_read_ = color_json_read['warning-color'] # orange | black
            return (QtGui.QColor(self.color_json_read_[0], self.color_json_read_[1], self.color_json_read_[2]), QtGui.QColor(0, 0, 0))
        elif int(flag) == 4:  # INFO
            self.color_json_read_ = color_json_read['info-color'] # green | white
            return (QtGui.QColor(self.color_json_read_[0], self.color_json_read_[1], self.color_json_read_[2]), None)
        elif int(flag) == 8:  # DEBUG
            self.color_json_read_ = color_json_read['debug-color'] # blue | white
            return (QtGui.QColor(self.color_json_read_[0], self.color_json_read_[1], self.color_json_read_[2]), None)
        elif int(flag) == 16:  # VERBOSE
            self.color_json_read_ = color_json_read['verbose-color'] # grey | white
            return (QtGui.QColor(self.color_json_read_[0], self.color_json_read_[1], self.color_json_read_[2]), None)

    # This function filters all entrys that are written in the listview
    def filter_color_and_display(self, entry_i):
        global entries
        global filter_list
        global path_to_file

        self.finished_message = entry_i['formattedMessage']

        fg, bg = self.calcColor(entry_i['flag'])
        item_with_color = QtWidgets.QListWidgetItem(self.finished_message)
        item_with_color.setForeground(fg)
        if bg != None:
            item_with_color.setBackground(bg)
        self.loglist.addItem(item_with_color)
        filter_list.append(item_with_color)

    # this function is triggerd if a new file is opened.
    def open_file(self):
        global entries
        global filter_list
        global path_to_file

        self.color_json_refresh()

        # Open file Browser
        file, check = QtWidgets.QFileDialog.getOpenFileName(None, "MLV | Choose a Logfile",
                                                            "", "Raw Log (*.rawlog)")
        if check:
            path_to_file = str(file)
            self.loglist.clear()
            filter_list = []
            entries = []

            # progress bar
            self.completed = 0
            self.percent = 0
            with open(path_to_file, 'r') as fp:
                for self.percent, line in enumerate(fp):
                    pass
            self.percent = self.percent / 19
            self.percent = round((1 * self.percent) / 100)

            # real logviewer part
            logfile_open = open(path_to_file, "rb")  # open log

            self.progress = QtWidgets.QProgressBar(self)
            self.progress.setGeometry(0, 160, 1415, 40)
            self.progress.show()

            while True:
                # Unpacks the rawlog file and strips down the values
                acht_bytes = logfile_open.read(8)
                if len(acht_bytes) != 8:
                    break

                jason_read_len = struct.unpack("!Q", acht_bytes)
                jason_read_len = jason_read_len[0]
                block_output = logfile_open.read(jason_read_len)
                if len(block_output) != jason_read_len:
                    raise Exception("File Corupt")

                decoded = json.loads(str(block_output, "UTF-8"))
                entries.append(decoded)
                self.filter_color_and_display(decoded)

                self.completed += self.percent
                self.progress.setValue(self.completed)

            self.progress.hide()
            self.progress.setValue(0)

    # this function is used to show every entry with that search word contained
    def search_input_submit_(self):
        global entries
        global filter_list
        global path_to_file

        self.lower_or_uppercase = self.lower_uper_case_switch.isChecked()

        self.check_list = []

        self.loglist.clear()
        self.search_string = str(self.search_input.text())

        # everything in lowercase
        if self.lower_or_uppercase == True:
            self.search_string = self.search_string.lower()

            if entries != None and entries != []:
                if self.search_string != None:
                    for i in range(len(entries)):
                        self.entry_index = entries[i]
                        self.containing_message = self.entry_index['formattedMessage']
                        self.containing_message = self.containing_message.lower()

                        if self.search_string in self.containing_message:
                            self.filter_color_and_display(self.entry_index)
                            self.check_list.append(" ")
                        else:
                            pass

                    if len(self.check_list) <= 0:
                        self.item_with_color = QtWidgets.QListWidgetItem(
                            'Theres NO entry that contains "' + str(self.search_string) + '"!')
                        self.item_with_color.setForeground(
                            QtGui.QColor(255, 255, 255))  # grey
                        self.loglist.addItem(self.item_with_color)

                    else:
                        pass  # error
                else:
                    pass  # error
            else:
                self.item_with_color = QtWidgets.QListWidgetItem(
                    "PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(
                    QtGui.QColor(255, 111, 102))  # grey
                self.loglist.addItem(self.item_with_color)

        elif self.lower_or_uppercase == False:  # everything like it used to be
            if entries != None and entries != []:
                if self.search_string != None:
                    for i in range(len(entries)):
                        self.entry_index = entries[i]
                        self.containing_message = self.entry_index['formattedMessage']

                        if self.search_string in self.containing_message:
                            self.filter_color_and_display(self.entry_index)
                            self.check_list.append(" ")
                        else:
                            pass

                    if len(self.check_list) <= 0:
                        self.item_with_color = QtWidgets.QListWidgetItem(
                            'Theres NO entry that contains"' + str(self.search_string) + '"!')
                        self.item_with_color.setForeground(
                            QtGui.QColor(233, 233, 233))  # grey
                        self.loglist.addItem(self.item_with_color)
                    else:
                        pass
                else:
                    pass
            else:
                self.item_with_color = QtWidgets.QListWidgetItem(
                    "PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(
                    QtGui.QColor(255, 111, 102))  # red
                self.loglist.addItem(self.item_with_color)
        else:
            pass  # ERROR

    # a function to create labels where and how you want
    def create_status_label_status(self, message, where, y, x):
        global settings_window_create

        where.color_status_label = QtWidgets.QLabel(where)
        where.color_status_label.setText(message)
        where.color_status_label.move(x, y)
        where.color_status_label.show()

    #function returning and compare values
    def compare_and_return(self, combobox_val, val_to_compare, val_to_change):
            if combobox_val == val_to_compare:
                self.data[val_to_change] = settings_window_create.rgb_value

    # a function to get color input and change it!
    def Submit_color_chosen_(self):
        global settings_window_create
        global color_json_read

        settings_window_create.color_input = str(
            settings_window_create.Submit_color_chosen_input.text())  # get color to change to
        settings_window_create.combobox_value_color = str(
            settings_window_create.target_color_to_change.currentText())  # get item to change

        if len(settings_window_create.color_input) == 7 and settings_window_create.color_input.startswith('#'):
            # settings_window_create.combobox_value_color
            settings_window_create.color_input = settings_window_create.color_input[1:]
            settings_window_create.rgb_value = list(
                int(settings_window_create.color_input[i:i+2], 16) for i in (0, 2, 4))

            with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "r") as jsonFile:
                self.data = json.load(jsonFile)

            # asign changed value
            self.compare_and_return(settings_window_create.combobox_value_color, "Background color", 'background-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "Nav Background color", 'nav-background-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "[INFO] color", 'info-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "[VERBOSE] color", 'verbose-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "[ERROR] color", 'error-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "[DEBUG] color", 'debug-color')
            self.compare_and_return(settings_window_create.combobox_value_color, "[WARNING] color", 'warning-color')

            with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "w") as jsonFile:
                json.dump(self.data, jsonFile)

            #status (successfull)
            self.create_status_label_status(
                "Successfully changed!", settings_window_create, 60, 160)
            
        else:
            #status (unsuccessfull)
            self.create_status_label_status(
                "Something went wrong!", settings_window_create, 60, 160)
            print("ERROR 320")  # build error/num error

        self.color_json_refresh()
    
    #A function that writes a new query in a json file
    def preset_submit_query_(self):
        global settings_window_create

        settings_window_create.query_input = str(
            settings_window_create.preset_query_input.text())  # get query
        
        if len(settings_window_create.query_input) >= 0:
            with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "r") as jsonFile:
                self.data = json.load(jsonFile)

                self.preset_query_list = self.data["preset_querys"]
                self.preset_query_list.append(settings_window_create.query_input)
                self.data["preset_querys"]  = self.preset_query_list

            with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "w") as jsonFile:
                json.dump(self.data, jsonFile)
                #status (successfull)
                self.create_status_label_status(
                    "Added succesfully!", settings_window_create, 270, 160)
                self.use_preset_query_drp.addItem(settings_window_create.query_input)
        else:
            #status (unsuccessfull)
            self.create_status_label_status(
                "Something went wrong!", settings_window_create, 270, 160)
            

    # this function is for controling color etc
    def settings_submit_(self):
        global num_of_settings_window_create
        global settings_window_create

        if num_of_settings_window_create == 1:
            settings_window_create = QtWidgets.QWidget(self)
            settings_window_create.setGeometry(400, 200, 400, 200)
            settings_window_create.setStyleSheet(
                "border-radius: 4px; background-color: #efefef;")

            uifile_ = os.path.join(os.path.dirname(
                sys.argv[0]), "ui_files/settings.ui")
            uic.loadUi(uifile_, settings_window_create)

            settings_window_create.close_settigns_button.clicked.connect(
                self.settings_submit_)  # X button
            settings_window_create.Submit_color_chosen.clicked.connect(
                self.Submit_color_chosen_)  # color submit button
            settings_window_create.submit_query.clicked.connect(
                self.preset_submit_query_) #query submit button

            settings_window_create.color_input = settings_window_create.findChild(
                QtWidgets.QLineEdit, 'Submit_color_chosen_input')
            settings_window_create.preset_query_input = settings_window_create.findChild(
                QtWidgets.QLineEdit, 'query_preset_input')

            self.create_status_label_status("Background color: "+str(color_json_read['background-color'])+"; Nav Background color: "+str(color_json_read['nav-background-color'])+";", settings_window_create, 180, 10)
            self.create_status_label_status("[VERBOSE] color: "+str(color_json_read['verbose-color']) + ";  [INFO] color: "+str(color_json_read['info-color'])+";",  settings_window_create, 200, 10)
            self.create_status_label_status("[WARNING] color: "+str(color_json_read['warning-color'])+";  [ERROR] color: "+str(color_json_read['error-color']) + ";",  settings_window_create, 220, 10)
            self.create_status_label_status("[DEBUG] color: "+str(color_json_read['debug-color'])+"; (RGB)", settings_window_create, 240, 10)

            settings_window_create.show()
            num_of_settings_window_create += 1

        elif num_of_settings_window_create == 2:
            settings_window_create.hide()
            if 'settings_window_create.status_label' in locals():
                settings_window_create.status_label.hide()
            num_of_settings_window_create -= 1
        else:
            print("ERROR 320")  # build error/num error

    #this function is used to safe a querry into the settings file
    def save_into_settings(self, val):
        with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "r") as jsonFile:
            self.data = json.load(jsonFile)

            self.data["preset_querys"].append(val)

        with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "w") as jsonFile:
            json.dump(self.data, jsonFile)
            #status (successfull)

    #this function is used to execute the preset query
    def preset_query_submit(self, value):
        if self.use_preset_query_drp.currentText() != "Choose a query...":
            if entries != []:
                for i in range(len(entries)):
                    return_val = run(self.use_preset_query_drp.currentText(), entries[i])
                    
                    #filter entries
                    filter_list[i].setHidden(not return_val)

    # this function is used to process your code :)
    def code_input_submit_(self):
        global entries
        global filter_list
        global path_to_file

        self.code_input_ = str(self.code_input.text())

        #if(flag == ERROR){ true } else {false} (sample query)
        if "ERROR" in self.code_input_ or "DEBUG" in self.code_input_ or "INFO" in self.code_input_ or "WARNING" in self.code_input_ or "VERBOSE" in self.code_input_and and len(self.code_input) <= 17: #use own query
            self.code_input_ = "if(" + self.code_input_ + "){ true } else {false} (sample query)"
        elif self.code_input_[-1] != ";" and self.code_input_[-1]  != "}": 
            self.code_input_ = self.code_input_ + ";"
        else: 
            pass

        for i in range(len(entries)):
            return_val = run(self.code_input_, entries[i])

            #filter entries
            filter_list[i].setHidden(not return_val)

        self.save_into_settings(self.code_input_) #save preset query
        self.use_preset_query_drp.addItem(self.code_input_)

# mainapp run
application_run = QtWidgets.QApplication(sys.argv)
Main_application = Main_Ui()
Main_application.show()
application_run.exec_()