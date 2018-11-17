'''
 frontend.py
 User interface for ScreenDoorSDP
 Author: David Greeson
 Created: 10/22/2018
 Last Modified By: David Greeson
 Last Modified: 11/08/2018
'''

import wx, gnsq, time, pyautogui
from threading import Thread
from datetime import datetime

call_rec_reader = gnsq.Reader('call_received', 'frontend_lcd', '127.0.0.1:4150')
hist_give_reader = gnsq.Reader('history_give', 'frontend_lcd', '127.0.0.1:4150')
set_all_reader = gnsq.Reader('settings_all', 'frontend_lcd', '127.0.0.1:4150')
set_give_reader = gnsq.Reader('setting_give', 'frontend_lcd', '127.0.0.1:4150')

global CALL_INC, CALL_REC_MSG, HIST_GIVE_MSG, SET_ALL_MSG, SET_GIVE_MSG
CALL_INC = False
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
                                  307:'alt',
                                  347:'f8',
                                  348:'f9',
                                  349:'f10',
                                  350:'f11',
                                  351:'f12'}

        self.conn = gnsq.Nsqd(address='127.0.0.1',http_port=4151)

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
        self.end_of_call_history = False
        self.waiting_for_message = False

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

        # Ask the backend for a call history of 10 elements to start with
        self.setupCallHistory()

    @call_rec_reader.on_message.connect
    def call_rec_handler(reader, message):
        global CALL_REC_MSG, CALL_INC
        CALL_REC_MSG = message.body
        CALL_INC = True
        time.sleep(2)
        print 'Got call received message: {}'.format(message.body)
        pyautogui.press('f9')
        print 'Displaying caller info and waiting 30 sec...'
        time.sleep(30)
        print 'Displaying original menu again'
        pyautogui.press('f8')

    @hist_give_reader.on_message.connect
    def hist_give_handler(reader, message):
        global HIST_GIVE_MSG
        HIST_GIVE_MSG = message.body
        print 'Got history give message: {}'.format(message.body)
        time.sleep(2)
        pyautogui.press('f10')

    @set_all_reader.on_message.connect
    def set_all_handler(reader, message):
        global SET_ALL_MSG
        SET_ALL_MSG = message.body
        print 'Got settings all message: {}'.format(message.body)
        time.sleep(2)
        pyautogui.press('f11')

    @set_give_reader.on_message.connect
    def set_give_handler(reader, message):
        global SET_GIVE_MSG
        SET_GIVE_MSG = message.body
        print 'Got setting give message: {}'.format(message.body)
        time.sleep(2)
        pyautogui.press('f12')

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
        reader_objs = [call_rec_reader, hist_give_reader, set_all_reader, set_give_reader]

        for reader_thread in reader_threads:
            t = Thread(target=reader_thread)
            t.daemon = True
            t.start()

        for reader_obj in reader_objs:
            reader_obj.join()

    def sendMessage(self, topic, message, wait):
        if wait:
            self.waiting_for_message = True
        print 'Sending message:{} to topic:{}'.format(message,topic)
        self.conn.publish(topic,message)

    def setupGUIElements(self):
        # Create all three textboxes and position them with a little space
        # between each one to accentuate each one
        self.firstTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,0),size=(800,152))
        self.firstTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.secondTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,155),size=(800,152))
        self.secondTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.thirdTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,310),size=(800,170))
        self.thirdTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

    def loadCallHistory(self, num_entries=5): 
        global CALL_INC
        CALL_INC = False
        self.menu_items_list = ['                                \nSettings\n                                ']
        self.menu_ptr = 1
        self.current_selected_text_box = 0
        self.current_top_ptr = 1
        self.using_settings = False
        self.end_of_call_history = False
        self.sendMessage('history_get','10:0',False)

        self.firstTextBox.SetValue(self.menu_items_list[1])
        self.secondTextBox.SetValue(self.menu_items_list[2])
        self.thirdTextBox.SetValue(self.menu_items_list[3])
	
        # highlight the currently selected menu item
        self.highlightBox(self.firstTextBox)

    def setupCallHistory(self):
	'''
	function:
	    setupCallHistory: function to request the call history from the backend
                         and dipslay them on the screen.

	args:
	    num_calls: the number of calls to request from the backend. Default
                   is 5

	returns:
	    None

	raises:
	    None

	'''
        self.sendMessage('history_get','10:0',True)
	
        # Bind all 3 textboxes to go to the keyEventHandler whenever a key
        # is pressed down
        self.firstTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)
        self.secondTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)
        self.thirdTextBox.Bind(wx.EVT_KEY_DOWN, self.keyEventHandler)

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

    def formatMenuItem(self, number, name, time):
        number = '        {} ({}) {} - {}      '.format(number[:1],number[1:4],number[4:7],number[-4:])
        num_pad_spaces = int((32 - len(name))/2)
        space = ''
        for _ in range(num_pad_spaces):
            space = space + ' '
        name = '{}{}{}'.format(space,name,space)
        num_pad_spaces = int((32 - len(time))/2)
        space = ''
        for _ in range(num_pad_spaces):
            space = space + ' '
        time = '{}{}{}'.format(space,time,space)
        return '{}\n{}\n{}'.format(number,name,time)
        

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
	
        global CALL_INC, CALL_REC_MSG, HIST_GIVE_MSG, SET_ALL_MSG, SET_GIVE_MSG
        # Get the event code
        code = event.GetKeyCode()

        # If the event is an up arrow key pressed...
        if self.key_by_ascii_dict[code] == 'up':
            if not CALL_INC:
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
            if not CALL_INC:
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
                elif not self.end_of_call_history and not self.waiting_for_message:
                    self.sendMessage('history_get','10:{}'.format(len(self.menu_items_list)-1),True)

                # Update the values in the text boxes
                self.setValues()

        if self.key_by_ascii_dict[code] == 'enter':
            if CALL_INC:
                self.sendMessage('call_blacklist',CALL_REC_MSG,False)
                self.thirdTextBox.SetValue('Caller Has Been Blocked!')
            elif self.menu_ptr == 0:
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

        if self.key_by_ascii_dict[code] == 'f8':
            self.loadCallHistory()

        if self.key_by_ascii_dict[code] == 'f9':
            msg_list = CALL_REC_MSG.split(':')
            self.firstTextBox.SetValue('\nIncoming Call From')
            self.secondTextBox.SetValue('{}\n{}'.format(msg_list[0],msg_list[1]))
            self.thirdTextBox.SetValue(u'Press the \u2713 button to block this caller!')

        if self.key_by_ascii_dict[code] == 'f10':
            msg_list = HIST_GIVE_MSG.split(':')
            if msg_list[0] == '0':
                self.end_of_call_history = True
                self.menu_items_list.append('                                \nEnd of Call History\n                                ')
            else:
                for item in range(2,int(msg_list[0])+2):
                    sub_msg_list = msg_list[item].split(';')
                    self.menu_items_list.append(self.formatMenuItem(sub_msg_list[0],sub_msg_list[1],sub_msg_list[2]))
            self.waiting_for_message = False
            self.setValues()

        if self.key_by_ascii_dict[code] == 'f11':
            print 'got the f11'

        if self.key_by_ascii_dict[code] == 'f12':
            print 'got the f12'

# If running this program by itself (Please only do this...)
if __name__ == '__main__':

    # Create an instance of a wx Application
    app = wx.App()

    # Create an instance of the FrontEnd class and show the GUI
    window = FrontEnd(None, title='Screen Door')
    window.Show()

    # Do Forever Loop
    app.MainLoop()
