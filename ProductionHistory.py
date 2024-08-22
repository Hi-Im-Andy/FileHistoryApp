#!/bin/env python3

'''
Single program file that would be used to upload files from the customer to the production history folder.
'''

import os
import shutil
import logging
from datetime import datetime
import customtkinter as ctk
from logging.handlers import RotatingFileHandler
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES

__author__ = "Andy Hernandez"
__date__ = "08/05/2024"
__status__ = "Demo"
__version__ = "1.1"

#############################################################
# Main App
#############################################################
# ctk.set_appearance_mode("system")
# ctk.set_appearance_mode("dark")
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# This should be changed based on the shared directory for a team.
DIR = f"C:/Users/{os.getlogin()}/Desktop"

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    '''
    Main app display window

    Args:
        ctk.CTk (class): The parent class derived from customtkinter
        TkinterDnD.DnDWrapper: The parent class for the drag and drop

    Returns:
        None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.TkdndVersion = TkinterDnD._require(self)

        self.user = os.getlogin()
        self.log = make_log()
        self.log.info(f"App opened by {self.user}")

        self.title("Production History Upload")
        self.geometry("670x875")
        self.resizable(False, False)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        self.titleLabel = ctk.CTkLabel(self, text = "Production History", font = ("Roboto", 30))
        self.titleLabel.grid(row = 0, column = 0, rowspan = 1, columnspan = 6, padx = 10, pady = 00, sticky = "nsew")

        # Create inputs for tool# and work order number
        self.tool_frame = ToolFrame(self)
        self.tool_frame.grid(row = 1, column = 0, rowspan = 1, columnspan = 9, padx = 20, pady = 0, sticky = "nsew")

        # Create Options
        self.options_frame = OptionsFrame(self)
        self.options_frame.grid(row = 2, column = 5, rowspan = 10, columnspan = 2, padx = 20, pady = 20, sticky = "nsew")

        # Create File uploads
        self.file_frame = FileFrame(self)
        self.file_frame.grid(row = 2, column = 0, rowspan = 12, columnspan = 4, padx = 20, pady = 20, sticky = "nsew")

        # Buttons
        self.uploadButton = ctk.CTkButton(self, text = "Upload", command = self.upload)
        self.uploadButton.grid(column = 5, row = 12, columnspan = 1, padx = 20, pady = 20, sticky = "nsew")

        self.closeButton = ctk.CTkButton(self, text = "Close", command = self.close)
        self.closeButton.grid(column = 5, row = 13, columnspan = 1, padx = 20, pady = 20, sticky = "nsew")

        self.errorEntry = ctk.CTkEntry(self, placeholder_text = "Error:", text_color = "red", state = "disabled")
        self.errorEntry.grid(column = 0, row = 14, columnspan = 6, padx = 20, pady = 20, sticky = "nsew")

#############################################################
# App Functions (Button functions etc)
#############################################################
    def upload(self):
        '''
        Gathers all of the users inputs, creates the folder structure, and places files accordingly

        Args:
            none

        Returns:
            none
        '''
        self.log.info("Uploading")
        tool = self.tool_frame.toolEntry.get()
        work_order = self.tool_frame.workOrderEntry.get()
        self.tool_frame.tool.set(tool)
        self.tool_frame.work_order.set(work_order)

        if (not self.checkInputs(tool, work_order)):
            self.updateError("Tool or Workorder is incorrect")
            return
        if (self.options_frame.requiredCheck.get() == "no"):
            print("Required files not uploaded")
            self.updateError("Required files are not uploaded (check box)")
            return
        if (len(self.file_frame.in_frame.paths) < 1 or len(self.file_frame.out_frame.paths) < 1):
            print("No files uploaded on either inside or outside")
            self.updateError("No files were uploaded inside, outside, or both.")
            return
        
        self.log.debug("Checks done")

        try:
            self.log.debug("Uploading")
            createFolderStructure(tool, work_order)
            self.log.debug("Folder structure created, uploading files")
            self.uploadFiles()
            self.log.debug("Files uploaded")
            self.destroy()
        except Exception as e:
            self.log.error(f"Upload failed: {e}")

    def checkInputs(self, tool, work_order):
        '''
        Checks to see if the tool and work order are normal

        Args:
            tool (str): The tool that was input
            work_order (str): The work order that was input

        Returns:
            bool: True if the check passed and false if the check did not
        '''
        if (not tool or tool == "Null") or (not work_order or work_order == "Null"):
            self.log.debug(f"Tool({tool}) or workorder({work_order}) not filled in")
            return False
        
        if ((len(tool) != 5) or (not str(tool).isdigit())):
            self.log.debug(f"Tool({tool}) does not seem correct")
            dialog = ctk.CTkInputDialog(text = "Tool number does not seem correct, retype the tool number to confirm.")
            if (dialog.get_input() == tool):
                self.log.debug(f"Tool confirmed")
                return True
            return False
        
        if (len(work_order) != 8):
            self.log.debug(f"Workorder({work_order}) does not seem correct, check length")
            dialog = ctk.CTkInputDialog(text = "Work order does not seem correct, retype the work order to confirm.")
            if (dialog.get_input() == work_order):
                self.log.debug(f"Workorder confirmed")
                return True
            return False
        return True

    def uploadFiles(self):
        '''
        Places the users selected files into the new directory

        Args:
            None

        Returns:
            None
        '''
        tool = self.tool_frame.tool.get()
        work_order = self.tool_frame.work_order.get()
        in_paths = self.file_frame.in_frame.paths
        out_paths = self.file_frame.out_frame.paths

        folder_dst = os.path.join(DIR, tool)
        folder_dst = os.path.join(folder_dst, "02 - Work Orders")
        wo_folder_dst = os.path.join(folder_dst, work_order)

        # STOCK ORDER_MM.DD.YY
        if (self.options_frame.order_type.get() == 3):
            date = datetime.now().strftime("%m.%d.%Y")
            wo_folder_dst = os.path.join(wo_folder_dst, f"STOCK ORDER_{date}")
            os.mkdir(wo_folder_dst)

        for path in in_paths:
            file = os.path.basename(path)
            file_dst = os.path.join(wo_folder_dst, file)
            shutil.copy2(path, file_dst)

        for path in out_paths:
            file = os.path.basename(path)
            file_dst = os.path.join(folder_dst, file)
            shutil.copy2(path, file_dst)

    def updateError(self, message : str):
        '''
        Updates the error label with the given message

        Args:
            message (str): The message that will be displayed in the error box

        Returns:
            None
        '''
        self.errorEntry.configure(state = "normal")
        self.errorEntry.delete("0", "end")
        self.errorEntry.insert("0", message)
        self.errorEntry.configure(state = "disabled")

    def close(self):
        '''
        Closes the main window

        Args:
            None

        Returns:
            None
        '''
        self.log.debug(f"App closed by {self.user}")
        self.destroy()

#############################################################
# App Sections
#############################################################
# Tool and Work order
class ToolFrame(ctk.CTkFrame):
    '''
    Sub class for the tool and work-order entry section

    Args:
        self (ctk.CTkFrame): The parent class

    Returns:
        None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tool = ctk.StringVar(value = "Null")
        self.work_order = ctk.StringVar(value = "Null")

        self.toolEntry = ctk.CTkEntry(self, placeholder_text = "Tool #")
        self.toolEntry.grid(column = 0, row = 0, padx = 40, pady = 20)

        self.workOrderEntry = ctk.CTkEntry(self, placeholder_text = "Work Order #", width = 200)
        self.workOrderEntry.grid(column = 2, row = 0, columnspan = 2, padx = 40, pady = 20)

# Options
class OptionsFrame(ctk.CTkFrame):
    '''
    Sub class for the option selection section

    Args:
        self (ctk.CTkFrame): The parent class

    Returns:
        None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.repeat = ctk.StringVar(value = "no")
        self.order_type = ctk.IntVar(value = 0)

        self.typeCheck = ctk.CTkCheckBox(self, text = "Repeat", variable = self.repeat, onvalue = "yes", offvalue = "no")
        self.typeCheck.grid(column = 0, row = 0, padx = 20, pady = 20, sticky = "nsew")

        self.itarRadio = ctk.CTkRadioButton(self, text = "ITAR", variable = self.order_type, value = 1)
        self.itarRadio.grid(column = 0, row = 1, padx = 20, pady = 20, sticky = "nsew")

        self.nonItarRadio = ctk.CTkRadioButton(self, text = "Non-ITAR", variable = self.order_type, value = 2)
        self.nonItarRadio.grid(column = 0, row = 2, padx = 20, pady = 20, sticky = "nsew")

        self.stockRadio = ctk.CTkRadioButton(self, text = "Stock", variable = self.order_type, value = 3)
        self.stockRadio.grid(column = 0, row = 3, padx = 20, pady = 20, sticky = "nsew")
        
        self.requiredCheck = ctk.CTkCheckBox(self, text = "Required Files", onvalue = "yes", offvalue = "no")
        self.requiredCheck.grid(column = 0, row = 4, padx = 20, pady = 20, sticky = "nsew")

        # self.required1Button = ctk.CTkButton(self, text = "Required 1", height = 40)
        # self.required1Button.grid(column = 0, row = 4, padx = 20, pady = 20, sticky = "nsew")

        # self.required2Button = ctk.CTkButton(self, text = "Required 2", height = 40)
        # self.required2Button.grid(column = 0, row = 5, padx = 20, pady = 20, sticky = "nsew")

# Files
class FileFrame(ctk.CTkFrame):
    '''
    Sub class for the File input and display section

    Args:
        ctk.CTkFrame: The parent class for the frame

    Returns:
        None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.files = ctk.StringVar(value = '')
        self.currentFile = ctk.StringVar(value = '')
        self.paths = []

        # Title Label
        self.fileLabel = ctk.CTkLabel(self, text = "Select Work Order Files", font = ("Roboto", 20))
        self.fileLabel.grid(column = 0, columnspan = 4, row = 0, padx = 20, pady = 20, sticky = "nsew")

        # File Display
        self.displayBox = ctk.CTkTextbox(self, width = 300, height = 200)
        self.displayBox.grid(column = 0, row = 4, rowspan = 6, columnspan = 4, padx = 20, pady = 20, sticky = "nsew")
        self.displayBox.delete("0.0", "end")
        self.displayBox.insert("0.0", "No Files")
        self.displayBox.configure(state = "disabled")

        # Inside Upload
        self.in_frame = inFrame(self, self.displayBox)
        self.in_frame.grid(row = 1, column = 3, rowspan = 3, columnspan = 1, padx = 20, pady = 20, sticky = "nsew")

        # Outside upload
        self.out_frame = outFrame(self, self.displayBox)
        self.out_frame.grid(row = 1, column = 1, rowspan = 3, columnspan = 1, padx = 20, pady = 20, sticky = "nsew")

        # Clear Display Box
        self.clearButton = ctk.CTkButton(self, text = "Clear", command = self.textClear, width = 140, height = 40)
        self.clearButton.grid(column = 0, columnspan = 4, row = 10, padx = 20, pady = 20, sticky = "nsew")

    def textClear(self):
        '''
        Clears the text on the file display section and sets it to default

        Args:
            None

        Returns:
            None
        '''
        self.displayBox.configure(state = "normal")
        self.displayBox.delete("0.0", "end")
        self.displayBox.insert("0.0", "No Files")
        self.displayBox.configure(state = "disabled")

        self.in_frame.paths = []
        self.out_frame.paths = []

class inFrame(ctk.CTkFrame):
    '''
    Sub class for the File input and display section

    Args:
        ctk.CTkFrame: The parent class for the frame

    Returns:
        None
    '''
    def __init__(self, master, display, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.displayBox = display

        self.paths = []
        self.currentFile = None

        # Label
        self.insideLabel = ctk.CTkLabel(self, text = "Inside")
        self.insideLabel.grid(column = 0, row = 0, padx = 20, pady = 10)

        # Drag and drop
        self.dropinEntry = ctk.CTkEntry(self, placeholder_text = "Drop File", height = 40, state = "disabled")
        self.dropinEntry.grid(column = 0, row = 1, padx = 20, pady = 20)
        self.dropinEntry.drop_target_register(DND_FILES)
        self.dropinEntry.dnd_bind("<<Drop>>", self.dropFile)
        
        # Out Button
        self.inButton = ctk.CTkButton(self, height = 40, text = "Upload File", command = self.openFile)
        self.inButton.grid(column = 0, row = 2, padx = 20, pady = 20)

    def dropFile(self, event):
        '''
        Gets the path from the drop in option

        Args:
            event (object): The event triggered by the drop in option
        
        Returns:
            None
        '''
        filePath = event.data
        filePath = filePath.replace('{', '')
        filePath = filePath.replace('}', '')
        self.paths.append(filePath)
        self.currentFile = os.path.basename(filePath)
        self.textUpdate()

    def openFile(self):
        '''
        Gets the file from the file explorer input option

        Args:
            None

        Returns:
            None
        '''
        file_path = filedialog.askopenfilename()
        self.paths.append(file_path)
        self.currentFile = os.path.basename(file_path)
        self.textUpdate()

    def textUpdate(self):
        '''
        Updates the file display section to show the files that are going to be uploaded

        Args:
            None

        Returns:
            None
        '''
        file_name = self.currentFile

        files = self.displayBox.get("0.0", "end")

        if("No Files" in files):
            self.displayBox.configure(state = "normal")
            self.displayBox.delete("0.0", "end")
            self.displayBox.insert("0.0", f"Inside            {file_name}")
            self.displayBox.configure(state = "disabled")
        else:
            files = f"{files} \nInside            {file_name}"
            self.displayBox.configure(state = "normal")
            self.displayBox.delete("0.0", "end")
            self.displayBox.insert("0.0", files)
            self.displayBox.configure(state = "disabled")

class outFrame(ctk.CTkFrame):
    def __init__(self, master, display, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.displayBox = display

        self.paths = []
        self.currentFile = None

        # Label
        self.outLabel = ctk.CTkLabel(self, text = "Outside")
        self.outLabel.grid(column = 0, row = 0, padx = 20, pady = 10)

        # Drag and drop
        self.dropOutEntry = ctk.CTkEntry(self, placeholder_text = "Drop File", height = 40, state = "disabled")
        self.dropOutEntry.grid(column = 0, row = 2, padx = 20, pady = 20)
        self.dropOutEntry.drop_target_register(DND_FILES)
        self.dropOutEntry.dnd_bind("<<Drop>>", self.dropFile)
        
        # Out Button
        self.outButton = ctk.CTkButton(self, height = 40, text = "Upload File", command = self.openFile)
        self.outButton.grid(column = 0, row = 3, padx = 20, pady = 20)


    def dropFile(self, event):
        '''
        Gets the path from the drop in option

        Args:
            event (object): The event triggered by the drop in option
        
        Returns:
            None
        '''
        filePath = event.data
        filePath = filePath.replace('{', '')
        filePath = filePath.replace('}', '')
        self.paths.append(filePath)
        self.currentFile = os.path.basename(filePath)
        self.textUpdate()

    def openFile(self):
        '''
        Gets the file from the file explorer input option

        Args:
            None

        Returns:
            None
        '''
        file_path = filedialog.askopenfilename()
        self.paths.append(file_path)
        self.currentFile = os.path.basename(file_path)
        self.textUpdate()

    def textUpdate(self):
        '''
        Updates the file display section to show the files that are going to be uploaded

        Args:
            None

        Returns:
            None
        '''
        file_name = self.currentFile

        files = self.displayBox.get("0.0", "end")

        if("No Files" in files):
            self.displayBox.configure(state = "normal")
            self.displayBox.delete("0.0", "end")
            self.displayBox.insert("0.0", f"Outside         {file_name}")
            self.displayBox.configure(state = "disabled")
        else:
            files = f"{files} \nOutside         {file_name}"
            self.displayBox.configure(state = "normal")
            self.displayBox.delete("0.0", "end")
            self.displayBox.insert("0.0", files)
            self.displayBox.configure(state = "disabled")

#############################################################
# Backend
#############################################################
def createFolderStructure(tool, work_order):
    '''
    Creates the folder structure for the tool and work order in the Production History folder

    Args:
        tool (str): The tool number where this information is going to be created or added to
        work_order (str): The work order number where this information is going to be created or added

    Returns:
        None
    '''
    phdir = DIR
    
    # Create tool folder
    tool_path = os.path.join(phdir, tool)
    checkCreate(tool_path)

    # Creating 01 and 02 folders
    fe_path = os.path.join(tool_path, "01 Production Teams")
    wo_path = os.path.join(tool_path, "02 Customer File History")
    checkCreate(fe_path)
    checkCreate(wo_path)

    # Creates a folder for each team in 01 folder
    checkCreate(os.path.join(fe_path, "Team 1"))
    checkCreate(os.path.join(fe_path, "Team 2"))
    checkCreate(os.path.join(fe_path, "Team 3"))
    checkCreate(os.path.join(fe_path, "Team 4"))

    # Create Work Order number in 02 folder
    checkCreate(os.path.join(wo_path, work_order))

def checkCreate(folder):
    '''
    Checks a directory and creates it if it does not exist

    Args:
        None

    Returns:
        None
    '''
    if (not os.path.exists(folder)):
        os.mkdir(folder)  

#############################################################
# Logger
#############################################################
def make_log():
    '''
    Creates the log or allows for appending to the log.

    Args:
        None

    Returns:
        logger (var): The pointer variable to log file.
    '''
    logger = logging.getLogger(__name__)
    path = os.path.dirname(__file__)
    log_filename = os.path.join(path, "program.log")

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt = "%(asctime)s: %(levelname)-8s %(message)s", datefmt = "%d/%m/%Y %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        filename = log_filename,
        mode = 'a',
        maxBytes = 1024 * 1024,
        backupCount = 1,
        encoding = None,
        delay = 0
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

#############################################################
# If Main
#############################################################
if (__name__ == "__main__"):
    app = App()
    app.mainloop()