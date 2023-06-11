#!/usr/bin/python3

# MONAL LOG VIEWER | MLV

import sys
import json
import struct
import os
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from internals.interpreter import run

#tmolitor: custom completer, see here for reference: https://stackoverflow.com/a/36296644
class Completer(QtWidgets.QCompleter):
    # Add texts instead of replace
    def pathFromIndex(self, index):
        path = QtWidgets.QCompleter.pathFromIndex(self, index)
        current_parts = str(self.widget().lineEdit().text()).split(" ")
        if len(current_parts) > 1:
            path = '%s %s' % (" ".join(current_parts[:-1]), path)   # replace last part with selected completion
        return path

    # Add operator to separate between texts
    def splitPath(self, path):
        path = str(path.split(' ')[-1]).lstrip(' ')
        return [path]
    

#global values
filter_list = []
settings_window_create = None  # (settings_submit_)
color_json_read = None  # (setting all colors)


# A class used for logic and ui
class Main_Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        global color_json_read

        self.setFixedSize(1400, 840)

        uic.loadUi(os.path.join(os.path.dirname(
            sys.argv[0]), "ui_files/user_interface.ui"), self)
        self.setWindowTitle("Monal Log Viewer")
        self.setWindowIcon(QtGui.QIcon(os.path.join(
            os.path.dirname(sys.argv[0]), "monal_log_viewer.png")))

        self.color_json_refresh()

        # Buttons & Inputs
        self.open_file_browser.clicked.connect(self.open_file)
        self.search_input_submit.clicked.connect(self.search_input_submit_)
        self.settings_button.clicked.connect(self.settings_submit_)
        self.query_box_clear.clicked.connect(self.query_box_clear_)

        self.use_preset_query_drp.activated[str].connect(self.preset_query_submit)
        self.search_input = self.findChild(QtWidgets.QLineEdit, 'search_input')

    # This function is used to update all data
    def color_json_refresh(self):
        global color_json_read

        self.color_json_read_ = open(os.path.join(
            os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "rb")
        self.color_json_read_ = self.color_json_read_.read()
        self.color_json_read_ = json.loads(str(self.color_json_read_, "UTF-8"))
        color_json_read = self.color_json_read_

        # List background
        self.color_json_read_ = color_json_read['background-color']
        self.loglist.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
            self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); border: 0px solid black;")
        self.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
            self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #efefef;")

        # Toolbar background
        self.color_json_read_ = color_json_read['nav-background-color']
        if self.color_json_read_ >= [127, 127, 127]:
            self.widget_2.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
                self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #000;")
        else:
            self.widget_2.setStyleSheet("background-color:rgb(" + str(self.color_json_read_[0]) + "," + str(
                self.color_json_read_[1]) + "," + str(self.color_json_read_[2]) + "); color: #efefef;")
            
        # Dropdown settings
        self.use_preset_query_drp.clear()
        self.preset_query_list_app = color_json_read['preset_querys']
        self.use_preset_query_drp.addItem("")
        self.use_preset_query_drp.setEditable(True)
        self.use_preset_query_drp.setInsertPolicy(QtWidgets.QComboBox.InsertAtTop)
        for i in self.preset_query_list_app:
            self.use_preset_query_drp.addItem(i)

        #tmolitor: auto completion (this list is INCOMPLETE)
        completer = Completer(["ERROR", "WARN", "INFO", "DEBUG", "VERBOSE", "level", "message", "file", "line", "threadName", "fileName", "function", "threadID", "_counter", "__processID", "queueLabel", "timestamp", "threadID"])
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.use_preset_query_drp.setCompleter(completer)

    # A function that arranges color to entry flag
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

    # This function filters all entries
    def filter_color_and_display(self, entry_i):
        global filter_list

        self.finished_message = entry_i['formattedMessage']

        fg, bg = self.calcColor(entry_i['flag'])
        item_with_color = QtWidgets.QListWidgetItem(self.finished_message)
        item_with_color.setForeground(fg)
        if bg != None:
            item_with_color.setBackground(bg)
        self.loglist.addItem(item_with_color)
        filter_list.append(item_with_color)

    # This function is triggerd if a new file is opened
    def open_file(self):
        global filter_list

        # Open file Browser
        file, check = QtWidgets.QFileDialog.getOpenFileName(None, "MLV | Choose a Logfile",
                                                            "", "Raw Log (*.rawlog)")
        if check:
            self.color_json_refresh()
            self.path_to_file = str(file)
            self.loglist.clear()
            filter_list = []
            entries = []
            old_percentage = 0
            read_size = 0

            size = os.path.getsize(self.path_to_file)
            logfile_open = open(self.path_to_file, "rb")

            self.progress = QtWidgets.QProgressBar(self)
            self.progress.setGeometry(0, 140, 1415, 40)
            self.progress.show()

            while True:
                # Unwraps the rawlog file and strips down the values
                acht_bytes = logfile_open.read(8)
                if len(acht_bytes) != 8:
                    break

                json_read_len = struct.unpack("!Q", acht_bytes)
                json_read_len = json_read_len[0]
                block_output = logfile_open.read(json_read_len)
                if len(block_output) != json_read_len:
                    raise Exception("File Corupt")

                decoded = json.loads(str(block_output, "UTF-8"))
                entries.append(decoded)
                self.filter_color_and_display(decoded)

                read_size += json_read_len + 8
                current_percentage = int(read_size/size*100)

                if current_percentage != old_percentage:
                    self.progress.setValue(current_percentage)
                    old_percentage = current_percentage

            self.progress.hide()
            self.progress.setValue(0)

            logfile_open.close()

    # This function is used to show every entry with that search word contained
    def search_input_submit_(self):
        global filter_list

        self.lower_or_uppercase = self.lower_uper_case_switch.isChecked()

        self.check_list = []

        self.search_string = str(self.search_input.text())

        if self.lower_or_uppercase == True:
            self.search_string = self.search_string.lower()

            if self.entries != None and self.entries != []:
                if self.search_string != None:
                    for i in range(len(self.entries)):
                        self.entry_index = self.entries[i]
                        self.containing_message = self.entry_index['formattedMessage']
                        self.containing_message = self.containing_message.lower()

                        if self.search_string in self.containing_message:
                            filter_list[i].setHidden(False)
                            self.check_list.append(" ")
                        else:
                            filter_list[i].setHidden(True)

                    if len(self.check_list) <= 0:
                        self.item_with_color = QtWidgets.QListWidgetItem(
                            'Theres NO entry that contains "' + str(self.search_string) + '"!')
                        self.item_with_color.setForeground(
                            QtGui.QColor(255, 255, 255))  # grey
                        self.loglist.addItem(self.item_with_color)

                    else:
                        pass
                else:
                    pass
            else:
                self.item_with_color = QtWidgets.QListWidgetItem(
                    "PLEASE IMPORT A FILE BEFORE SEARCHING!")
                self.item_with_color.setForeground(
                    QtGui.QColor(255, 111, 102))  # grey
                self.loglist.addItem(self.item_with_color)

        elif self.lower_or_uppercase == False:
            if self.entries != None and self.entries != []:
                if self.search_string != None:
                    for i in range(len(self.entries)):
                        self.entry_index = self.entries[i]
                        self.containing_message = self.entry_index['formattedMessage']

                        if self.search_string in self.containing_message:
                            filter_list[i].setHidden(False)
                            self.check_list.append(" ")
                        else:
                            filter_list[i].setHidden(True)

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
            pass

    # A function used to create labels, at a given position
    def create_status_label_status(self, message, where, y, x):
        global settings_window_create

        where.color_status_label = QtWidgets.QLabel(where)
        where.color_status_label.setText(message)
        where.color_status_label.move(x, y)
        where.color_status_label.show()

    # This function compares two values 
    def compare_and_return(self, combobox_val, val_to_compare, val_to_change):
            if combobox_val == val_to_compare:
                self.data[val_to_change] = settings_window_create.rgb_value

    # This function is used to write input into the json file
    def Submit_color_chosen_(self):
        global settings_window_create
        global color_json_read

        settings_window_create.color_input = str(
            settings_window_create.Submit_color_chosen_input.text()) # This is the color to change
        settings_window_create.combobox_value_color = str(
            settings_window_create.target_color_to_change.currentText())  # This is the item to change

        if len(settings_window_create.color_input) == 7 and settings_window_create.color_input.startswith('#'):

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

            # Status (successfull)
            self.create_status_label_status(
                "Successfully changed!", settings_window_create, 60, 160)
            
        else:
            # Status (unsuccessfull)
            self.create_status_label_status(
                "Something went wrong!", settings_window_create, 60, 160)
            print("ERROR 320")  # build error/num error

        self.color_json_refresh()
    
    # A function that writes a new query in a json file
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
                # Status (successfull)
                self.create_status_label_status(
                    "Added succesfully!", settings_window_create, 270, 160)
                self.use_preset_query_drp.addItem(settings_window_create.query_input)
        else:
            # Status (unsuccessfull)
            self.create_status_label_status(
                "Something went wrong!", settings_window_create, 270, 160)
            

    # These are the settings
    def settings_submit_(self):
        global settings_window_create

        self.num_of_settings_window_create = 1

        if self.num_of_settings_window_create == 1:
            settings_window_create = QtWidgets.QWidget(self)
            settings_window_create.setGeometry(400, 200, 400, 200)
            settings_window_create.setStyleSheet(
                "border-radius: 4px; background-color: #efefef;")

            uifile_ = os.path.join(os.path.dirname(
                sys.argv[0]), "ui_files/settings.ui")
            uic.loadUi(uifile_, settings_window_create)

            settings_window_create.close_settigns_button.clicked.connect(
                self.settings_submit_)  # Escape button
            settings_window_create.Submit_color_chosen.clicked.connect(
                self.Submit_color_chosen_)  # Color submit button
            settings_window_create.submit_query.clicked.connect(
                self.preset_submit_query_) # Query submit button

            settings_window_create.color_input = settings_window_create.findChild(
                QtWidgets.QLineEdit, 'Submit_color_chosen_input')
            settings_window_create.preset_query_input = settings_window_create.findChild(
                QtWidgets.QLineEdit, 'query_preset_input')

            #print values onto the settings page
            self.create_status_label_status("Background color: "+str(color_json_read['background-color'])+"; Nav Background color: "+str(color_json_read['nav-background-color'])+";", settings_window_create, 180, 10)
            self.create_status_label_status("[VERBOSE] color: "+str(color_json_read['verbose-color']) + ";  [INFO] color: "+str(color_json_read['info-color'])+";",  settings_window_create, 200, 10)
            self.create_status_label_status("[WARNING] color: "+str(color_json_read['warning-color'])+";  [ERROR] color: "+str(color_json_read['error-color']) + ";",  settings_window_create, 220, 10)
            self.create_status_label_status("[DEBUG] color: "+str(color_json_read['debug-color'])+"; (RGB)", settings_window_create, 240, 10)

            settings_window_create.show()
            self.num_of_settings_window_create += 1

        elif self.num_of_settings_window_create == 2:
            settings_window_create.hide()
            if 'settings_window_create.status_label' in locals():
                settings_window_create.status_label.hide()
            self.num_of_settings_window_create -= 1
        else:
            print("ERROR 320")  # build error/num error

    # This function is used to safe a query into the settings file
    def save_into_settings(self, val):
        with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "r") as jsonFile:
            self.data = json.load(jsonFile)

            self.data["preset_querys"].append(val)

        with open(os.path.join(os.path.dirname(sys.argv[0]), "ui_files/settings.json"), "w") as jsonFile:
            json.dump(self.data, jsonFile)
            # Status (successfull)

    # This function is used to execute the query
    def preset_query_submit(self, value):
        if self.use_preset_query_drp.currentText() != "":

            if self.entries != []:
                for i in range(len(self.entries)):
                    return_val = run(self.use_preset_query_drp.currentText(), self.entries[i])
                    
                    # Filter all entries
                    filter_list[i].setHidden(not return_val)
                
                self.save_into_settings(self.use_preset_query_drp.currentText())

    # This function is used to clear the combobox
    def query_box_clear_(self):
        self.use_preset_query_drp.clearEditText()


# mainapp run
application_run = QtWidgets.QApplication(sys.argv)
Main_application = Main_Ui()
Main_application.show()
application_run.exec_()