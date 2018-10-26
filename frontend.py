'''
 frontend.py
 User interface for ScreenDoorSDP
 Author: David Greeson
 Created: 10/22/18
 Last Modified By: David Greeson
 Last Modified: 10/26/18
'''

import wx
from datetime import datetime

class FrontEnd(wx.Frame):
    '''
    FrontEnd class which contains the GUI and all of the elements involved in
    communicating between the user and the backend
    '''
    def __init__(self, parent, title):
        '''
        function:
            __init__: constructor for the FrontEnd calss. It calls the super()
                      constructor to build the GUI window, creates andn places
                      the rest of the GUI elements, declares class variables
                      to be used throughout this GUI, and loads the call history

        args:
            parent: The parentn object (using default)
            title: the title of the GUI which is passed in when creating the
                       FrontEnd object

        returns:
            None

        raises:
            None
        '''

	# Call the super class to build the GUI
        super(FrontEnd, self).__init__(parent,title=title, size=(800,480))

	# The key_by_ascii_dict is used to convert ascii characters into
        # easier to understand buttons on the keyboard
        self.key_by_ascii_dict = {314:'left',
                                  315:'up',
                                  316:'right',
                                  317:'down',
                                  13 :'enter',
                                  8  :'backspace',
                                  307:'alt'}

	# These 3 pointers help to keep up with what to display on the GUI.
        # menu_ptr is the list index of the currently selected menu item.
        # current_selected_text_box is an integer that ranges from 0 to 2
        # and represents which of the three textboxes on the screen has
        # the focus. current_top_ptr is an integer that represents the
        # index of the top most textbox's menu item
        self.menu_ptr = 1
        self.current_selected_text_box = 0
        self.current_top_ptr = 1

	# This is the menu list. It starts out with settings as the only
        # entry. New entries are appended after asking the backend for them
        self.menu_items_list = ['                                \nSettings\n                                ']

	# Center the GUI on the display
        self.Centre()

	# Load the other GUI elements
        self.setupGUIElements()

	# A dictionary so that I can dynamically use textboxes using only
	# an index for reference.
        self.text_box_num_dict = {0:self.firstTextBox,
                                  1:self.secondTextBox,
                                  2:self.thirdTextBox}

	# Ask the backend for a call history of 5 elements to start with
        self.loadCallHistory(5)

    def setupGUIElements(self):
	'''
	function:
	    setupGUIElements: function to create the rest of the necessary GUI
                              elements for displaying on the main window

	args:
	    None

	returns:
	    None

	raises:
	    None
	'''

	# Create all three textboxes and position them with a little space
	# between each one to accentuate each one
        self.firstTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,0),size=(800,152))
        self.firstTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.secondTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,155),size=(800,152))
        self.secondTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.thirdTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,310),size=(800,170))
        self.thirdTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

    def loadCallHistory(self, num_entries=5):
	'''
	function:
	    loadCallHistory: function to request the call history from the backend
                             and dipslay them on the screen.

	args:
	    num_calls: the number of calls to request from the backend. Default
                       is 5

	returns:
	    None

	raises:
	    None
	'''

	# NOTE: This function loads fake values until the backend is ready to 
        #       communicate with the frontend.
        now = datetime.now()
        ampm = 'pm' if now.hour >= 12 else 'am'
        self.menu_items_list.append(now.strftime('       %m/%d/%Y %I:%M ') + ampm + '      \nDavid Greeson\n       1 (336) 555 - 1234      ')
        for hour in range(23):
            date = datetime(2018,10,25,23-hour,0,0)
            ampm = 'pm' if date.hour >= 12 else 'am'
            self.menu_items_list.append(date.strftime('       %m/%d/%Y %I:%M ') + ampm +  '      \nGantt Chart\n       1 (919) 555 - 1234      ')
        for day in range(23):
            date = datetime(2018,10,25-day,6,0,0)
            self.menu_items_list.append(date.strftime('       %m/%d/%Y %I:%M') + ' am      \nGantt Chart\n       1 (919) 555 - 1234      ')

	# Load the textboxes with the first three call histories and ignore
        # the settings menu item at first.
        self.firstTextBox.AppendText(self.menu_items_list[1])
        self.secondTextBox.AppendText(self.menu_items_list[2])
        self.thirdTextBox.AppendText(self.menu_items_list[3])

	# Bind all 3 textboxes to go to the keyEventHandler whenever a key
        # is pressed down
        self.firstTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)
        self.secondTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)
        self.thirdTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)

	# highlight the currently selected menu item
        self.highlightBox(self.firstTextBox)

    def setValues(self):
	'''
	function:
	    setValues: function to set the values of all three textboxes based
                       on what the current_top_ptr is pointing to. It also
                       re-highlights the currently selected item

	args:
	    None

	returns:
	    None

	raises:
	    None
	'''

	# Load the menu items based on what the current_top_ptr is pointing to
        self.firstTextBox.SetValue(self.menu_items_list[self.current_top_ptr])
        self.secondTextBox.SetValue(self.menu_items_list[self.current_top_ptr+1])
        self.thirdTextBox.SetValue(self.menu_items_list[self.current_top_ptr+2])

	# re-highlight the currently selected item
        self.highlightBox(self.text_box_num_dict[self.current_selected_text_box])

    def highlightBox(self, textBox):
	'''
	function:
	    highlightBox: function to highlight the text within the textbox
                          that is passed in by reference

	args:
	    textBox: text box that is passed in by reference

	returns:
	    None

	raises:
	    None
	'''

	# Set focus on the current text box and highlight all text
        textBox.SetFocus()
        textBox.SetSelection(-1,-1)

    def keyEventHandler(self, event):
	'''
	function:
	    keyEventHandler: function that is called whenever a button
			     is pressed down

	args:
	    event: an event object that describes what event occurred

	returns:
	    None

	raises:
	    KeyError: a KeyError will be raised if a button other than 
                      the arrow keys, enter, backspace, or alt is 
                      pressed, however, this Error will be ignored.
	'''
	
	# Get the event code
        code = event.GetKeyCode()

	# If the event is an up arrow key pressed...
        if self.key_by_ascii_dict[code] == 'up':
	    # Only do anything if we are not at the top of the list.
	    # Decrement the pointers based on where we are in the GUI
            if self.menu_ptr != 0:
                if self.current_top_ptr == self.menu_ptr:
                    self.current_top_ptr-=1
                if self.current_selected_text_box != 0:
                    self.current_selected_text_box-=1
                self.menu_ptr-=1

		# Set the new values since we changed positions
                self.setValues()

	# If the event is a down arrow key pressed...
        if self.key_by_ascii_dict[code] == 'down':
	    # Only do anything if we are not at the bottom of the list.
	    # Increment the pointers based on where we are in the GUI.
            if self.menu_ptr < len(self.menu_items_list)-1:
                if self.menu_ptr - 2 == self.current_top_ptr:
                    self.current_top_ptr+=1
                if self.current_selected_text_box != 2:
                    self.current_selected_text_box+=1
                self.menu_ptr+=1

		# Set the new values since we changed positions
                self.setValues()

# If running this program by itself (Please only do this...)
if __name__ == '__main__':
    # Create an instance of a wx Application
    app = wx.App()

    # Create an instance of the FrontEnd class and show the GUI
    window = FrontEnd(None, title='Screen Door')
    window.Show()

    # Do Forever Loop
    app.MainLoop()
