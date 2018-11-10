'''
 frontend.py
 User interface for ScreenDoorSDP
 Author: David Greeson
 Created: 10/22/2018
 Last Modified By: David Greeson
 Last Modified: 11/08/2018
'''

import wx, gnsq, threading
from datetime import datetime

call_rec_reader = gnsq.Reader('call_received', 'call_rec', '127.0.0.1:4150')
hist_give_reader = gnsq.Reader('history_give', 'hist_give', '127.0.0.1:4150')
set_all_reader = gnsq.Reader('settings_all', 'set_all', '127.0.0.1:4150')
set_give_reader = gnsq.Reader('setting_give', 'set_give', '127.0.0.1:4150')

global CALL_REC, HIST_GIVE, SET_ALL, SET_GIVE, CALL_REC_MSG, HIST_GIVE_MSG, SET_ALL_MSG, SET_GIVE_MSG
CALL_REC = False
HIST_GIVE = False
SET_ALL = False
SET_GIVE = False
CALL_REC_MSG = ''
HIST_GIVE_MSG = ''
SET_ALL_MSG = ''
SET_GIVE_MSG = ''

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
            parent: The parent object (using default)
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
        # index of the top most textbox's menu item. using_settings is a
        # boolean value that represents using the settings menu or using
        # the main menu
        self.menu_ptr = 1
        self.current_selected_text_box = 0
        self.current_top_ptr = 1
        self.using_settings = False

	# This is the menu list. It starts out with settings as the only
        # entry. New entries are appended after asking the backend for them
        self.menu_items_list = ['                                \nSettings\n                                ']

        # THis is the settings list. It has generic settings right now
        self.settings_list = []
        for setting in range(8):
            self.settings_list.append('                                \nSetting {}\n                                '.format(setting))

	# Center the GUI on the display
        self.Centre()

	# Load the other GUI elements
        self.setupGUIElements()

        self.setupThreads()

	# A dictionary so that I can dynamically use textboxes using only
	# an index for reference.
        self.text_box_num_dict = {0:self.firstTextBox,
                                  1:self.secondTextBox,
                                  2:self.thirdTextBox}

	# Ask the backend for a call history of 5 elements to start with
        self.loadCallHistory(5)

    @call_rec_reader.on_message.connect
    def call_rec_handler(reader, message):
	global CALL_REC, CALL_REC_MSG
	CALL_REC_MSG = message.body
	CALL_REC = True
        print 'Got call received message: {}'.format(message.body)

    @hist_give_reader.on_message.connect
    def hist_give_handler(reader, message):
	global HIST_GIVE, HIST_GIVE_MSG
	HIST_GIVE_MSG = message.body
	HIST_GIVE = True
	print 'Got history give message: {}'.format(message.body)

    @set_all_reader.on_message.connect
    def set_all_handler(reader, message):
	global SET_ALL
	SET_ALL = True
	print 'Got settings all message: {}'.format(message.body)

    @set_give_reader.on_message.connect
    def set_give_handler(reader, message):
	global SET_GIVE
	SET_GIVE = True
	print 'Got setting give message: {}'.format(message.body)        

    def call_rec_reader_thread(self):
        call_rec_reader.start()

    def hist_give_reader_thread(self):
	hist_give_reader.start()

    def set_all_reader_thread(self):
	set_all_reader.start()

    def set_give_reader_thread(self):
	set_give_reader.start()

    def setupThreads(self):
        reader_threads = [self.call_rec_reader_thread, self.hist_give_reader_thread, self.set_all_reader_thread, self.set_give_reader_thread]

        for reader_thread in reader_threads:
            t = threading.Thread(target=reader_thread)
            t.daemon = True
            t.start()

	t = threading.Thread(target=self.checkForMessages)
	t.daemon = True
	t.start()

    def checkForMessages(self):
	global CALL_REC, HIST_GIVE, SET_ALL, SET_GIVE, CALL_REC_MSG, HIST_GIVE_MSG, SET_ALL_MSG, SET_GIVE_MSG
	while(True):
	    if CALL_REC:
	        CALL_REC = False
		msg_list = CALL_REC_MSG.split(':')
	        self.firstTextBox.SetValue('\nIncoming Call')
		self.secondTextBox.SetValue('\n{}'.format(msg_list[0]))
		self.thirdTextBox.SetValue('\n{}'.format(msg_list[1]))

	    if HIST_GIVE:
		HIST_GIVE = False
		msg_list = HIST_GIVE_MSG.split(':')
		for index in range(int(msg_list[0])):
		    entrys = msg_list[index+2].split(';')
		    self.menu_items_list.append('{}\n{}\n{}'.format(entrys[0],entrys[1],entrys[2]))
		self.firstTextBox.SetValue(self.menu_items_list[1])
		self.secondTextBox.SetValue(self.menu_items_list[2])
		self.thirdTextBox.SetValue(self.menu_items_list[3])

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
        
        list_to_use = self.settings_list if self.using_settings else self.menu_items_list

        # Load the menu items based on what the current_top_ptr is pointing to
        self.firstTextBox.SetValue(list_to_use[self.current_top_ptr])
        self.secondTextBox.SetValue(list_to_use[self.current_top_ptr+1])
        self.thirdTextBox.SetValue(list_to_use[self.current_top_ptr+2])

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

                # Update the values in the text boxes
                self.setValues()

	# If the event is a down arrow key pressed...
        if self.key_by_ascii_dict[code] == 'down':
            # Get the list to use
            list_to_use = self.settings_list if self.using_settings else self.menu_items_list
	    # Only do anything if we are not at the bottom of the list.
	    # Increment the pointers based on where we are in the GUI
            if self.menu_ptr < len(list_to_use)-1:
                if self.menu_ptr - 2 == self.current_top_ptr:
                    self.current_top_ptr+=1
                if self.current_selected_text_box != 2:
                    self.current_selected_text_box+=1
                self.menu_ptr+=1

		# Update the values in the text boxes
                self.setValues()

        if self.key_by_ascii_dict[code] == 'enter':
            if self.menu_ptr == 0:
                self.using_settings = True
                self.menu_ptr = 0
                self.current_selected_text_box = 0
                self.current_top_ptr = 0
                self.setValues()

        if self.key_by_ascii_dict[code] == 'backspace':
            if self.using_settings:
                self.using_settings = False
                self.menu_ptr = 1
                self.current_selected_text_box = 0
                self.current_top_ptr = 1
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
