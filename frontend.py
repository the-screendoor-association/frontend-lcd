'''
 frontend.py
 User interface for ScreenDoorSDP
 Author: David Greeson
 Created: 10/22/2018
 Last Modified By: David Greeson
 Last Modified: 11/08/2018
'''

import wx, gnsq, time, string
from threading import Thread
from multiprocessing import Process, Pipe
from datetime import datetime

# Global variables to let the timer function know to do something
global CALL_INC, UPDATE, CALL_REC, CALL_REC_MSG, LOAD_HIST
CALL_INC = False
UPDATE = False
CALL_REC = False
CALL_REC_MSG = ''
LOAD_HIST = False

class FrontEnd(wx.Frame):
    '''
    FrontEnd class which contains the GUI and all of the elements involved in
    communicating between the user and the backend
    '''
    def __init__(self, parent, title):
        '''
        function:
            __init__: constructor for the FrontEnd class. It calls the super()
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
        self.key_by_ascii_dict = {315:'up',
                                  317:'down',
                                  13:'enter',
                                  8:'backspace'}

        # Nsqd object used to transmit messages to localhost
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
        self.end_of_settings_ptr = 1
        self.using_settings = False
        self.end_of_call_history = False
        self.waiting_for_message = False
        self.selecting_setting = False
        self.state_name = ''

        # 32 spaces which is enough for a blank line
        self.line_space = 32*' '

        # This is the menu list. It starts out with settings as the only
        # entry. New entries are appended after asking the backend for them
        self.menu_items_list = ['{}\nSettings\n{}'.format(self.line_space,self.line_space)]

        # This is the settings list. It will contain settings upon request from user
        self.settings_list = []

        # This is the setting state list. It will contain states for a particular setting
        self.setting_state_list = []

        # Center the GUI on the display
        self.Centre()

        # Load the other GUI elements
        self.setupGUIElements()

        # A dictionary so that I can dynamically use textboxes using only
        # an index for reference.
        self.text_box_num_dict = {0:self.firstTextBox,
                                  1:self.secondTextBox,
                                  2:self.thirdTextBox}

        # Display a loading message until call history is loaded
        self.firstTextBox.SetValue('\nLoading Call History...')

        # Start the reader threads
        #self.setupThreads()
        self.reader_pipe, reader_child_pipe = Pipe()
        reader_proc = Process(target=self.readerThreads, args=(reader_child_pipe,))
        reader_proc.start()

        msg_proc = Thread(target=self.checkForMessages, args=(self.reader_pipe,))
        msg_proc.start()

        # Ask the backend for a call history of 10 elements to start with
        self.setupCallHistory()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(500)

    def onTimer(self, event):
        global UPDATE, CALL_REC, CALL_REC_MSG, LOAD_HIST
        if UPDATE:
            UPDATE = False
            self.setValues()

        elif CALL_REC:
            # Get the incoming call info, format it, and display it on the screen
            msg_list = CALL_REC_MSG.split(':')
            num = '{} ({}) {} - {}'.format(msg_list[0][:1],msg_list[0][1:4],msg_list[0][4:7],msg_list[0][-4:])
            self.firstTextBox.SetValue('\nIncoming Call From')
            self.secondTextBox.SetValue('{}\n{}'.format(msg_list[1],num))
            self.thirdTextBox.SetValue(u'Press the "Select" button to block this caller!')
            CALL_REC = False
            
        elif LOAD_HIST:
            self.selecting_setting = False
            self.using_settings = False
            self.firstTextBox.SetValue('\nLoading Call History...')
            self.secondTextBox.SetValue('')
            self.thirdTextBox.SetValue('')
            self.loadCallHistory()
            LOAD_HIST = False

        self.timer.Start(5)

    def checkForMessages(self, reader_pipe=None):
        global UPDATE, CALL_REC, CALL_REC_MSG, LOAD_HIST, CALL_INC
        while True:
            if reader_pipe.poll():
                msg = reader_pipe.recv()
                if msg[0] == 'hist_give':
                    # Make a list of all elements
                    msg_list = msg[1].split(':')
                    # If we receive an unrequested message history...
                    if msg_list[1] == '0' and not msg_list[0] == '0':
                        # Reset the menu pointers and reload the history
                        self.menu_items_list = ['{}\nSettings\n{}'.format(self.line_space,self.line_space)]
                        self.menu_ptr = 1
                        self.current_selected_text_box = 0
                        self.current_top_ptr = 1
                        self.using_settings = False
                        self.selecting_setting = False
                        self.end_of_call_history = False
                    
                    # If the backend says there's no more history...
                    if msg_list[0] == '0':
                        # Display "End of Call History" as the last element
                        self.end_of_call_history = True
                        self.menu_items_list.append('{}\nEnd of Call History\n{}'.format(self.line_space,self.line_space))
                    # Otherwise, ask for 10 more elements based on an offset of the last
                    # element that is loaded
                    else:
                        for item in range(2,int(msg_list[0])+2):
                            sub_msg_list = msg_list[item].split(';')
                            self.menu_items_list.append(self.formatMenuItem(sub_msg_list[0],sub_msg_list[1],sub_msg_list[2]))

                    # Indicate that the message is received and load the GUI values
                    self.waiting_for_message = False
                    UPDATE = True

                elif msg[0] == 'set_all':
                    # Make a list of all of the settings
                    msg_list = msg[1].split(':')
                    self.settings_list = []
                    # Format each setting and put them into the list
                    for setting in msg_list:
                        self.settings_list.append('{}\n{}\n{}'.format(self.line_space,setting,self.line_space))
                        self.end_of_settings_ptr += 1
                    self.settings_list.append('{}\nEnd of Settings\n{}'.format(self.line_space,self.line_space))

                    # Indicate that the message is received and load the GUI values
                    self.waiting_for_message = False
                    #self.setValues()
                    UPDATE = True

                elif msg[0] == 'set_give':
                    # Make a list of the setting states
                    msg_list = msg[1].split(':')

                    # Save the name of that state
                    self.state_name = msg_list[0]
                    self.setting_state_list = []

                    # Calculate the necessary space for the name and help message
                    name_pad_space = int((32 - len(msg_list[0]))/2)
                    help_pad_space = int((32 - len(msg_list[1]))/2)

                    # Append the name, help message, and current state as the first entry
                    self.setting_state_list.append('{}{}{}\nCurrently: {}\n{}{}{}'.format(name_pad_space*' ',msg_list[0],name_pad_space*' ',msg_list[2],help_pad_space*' ',msg_list[1],help_pad_space*' '))
                    
                    # Make a list of the states for that setting
                    states_list = msg_list[3].split(';')

                    # Append each state to the list
                    for state in states_list:
                        self.setting_state_list.append('{}\n{}\n{}'.format(self.line_space,state,self.line_space))
                    
                    # Add "End of List" as the last entry
                    self.setting_state_list.append('{}\nEnd of List\n{}'.format(self.line_space,self.line_space))
                    
                    # Indicate that the message has been received and load the GUI values
                    self.waiting_for_message = False
                    #self.setValues()
                    UPDATE = True

                elif msg[0] == 'call_rec':
                    CALL_INC = True
                    CALL_REC_MSG = msg[1]
                    CALL_REC = True
                    
                elif msg[0] == 'load_hist':
                    LOAD_HIST = True
                    
            time.sleep(0.05)

    def readerThreads(self, pipe):
        '''
        function:
            setupThreads: This function sets up and starts all of the reader threads

        args:
            None

        returns:
            None

        raises:
            None
        '''
        # All readers are declared globally so that they can be shared among threads
        call_rec_reader = gnsq.Reader('call_received', 'frontend_lcd', '127.0.0.1:4150')
        hist_give_reader = gnsq.Reader('history_give', 'frontend_lcd', '127.0.0.1:4150')
        set_all_reader = gnsq.Reader('settings_all', 'frontend_lcd', '127.0.0.1:4150')
        set_give_reader = gnsq.Reader('setting_give', 'frontend_lcd', '127.0.0.1:4150')

        global frontend_conn
        frontend_conn = pipe

        @call_rec_reader.on_message.connect
        def call_rec_handler(reader, message):
            '''
            function:
                call_rec_handler: This function handles what to do when a message
                                  from topic call_received is received

            args:
                reader: an instance of the reader object
                message: an object that contains the message

            returns:
                None

            raises:
                None
            '''
            global CALL_INC
            CALL_INC = True
            print 'Got call received message: {}'.format(message.body)
            frontend_conn.send(['call_rec',message.body])
            print 'Displaying caller info and waiting 30 sec...'
            time.sleep(30)
            print 'Displaying original menu again'
            frontend_conn.send(['load_hist','NULL'])

        @hist_give_reader.on_message.connect
        def hist_give_handler(reader, message):
            '''
            function:
                hist_give_handler: This function handles what to do when a message
                                   from topic history_five is received

            args:
                reader: an instance of the reader object
                message: an object that contains the message

            returns:
                None

            raises:
                None
            '''
            print 'Got history give message: {}'.format(message.body)
            frontend_conn.send(['hist_give',message.body])

        @set_all_reader.on_message.connect
        def set_all_handler(reader, message):
            '''
            function:
                set_all_handler: This function handles what to do when a message
                                 from topic settings_all is received

            args:
                reader: an instance of the reader object
                message: an object that contains the message

            returns:
                None

            raises:
                None
            '''
            print 'Got settings all message: {}'.format(message.body)
            frontend_conn.send(['set_all',message.body])

        @set_give_reader.on_message.connect
        def set_give_handler(reader, message):
            '''
            function:
                set_give_handler: This function handles what to do when a message
                                  from topic settings_give is received

            args:
                reader: an instance of the reader object
                message: an object that contains the message

            returns:
                None

            raises:
                None
            '''
            print 'Got setting give message: {}'.format(message.body)
            frontend_conn.send(['set_give',message.body])

        call_rec_reader.start(block=False)
        hist_give_reader.start(block=False)
        set_all_reader.start(block=False)
        set_give_reader.start()

    def sendMessage(self, topic, message, wait):
        '''
        function:
            sendMessage: This function sends a message to a specified topic

        args:
            topic: The topic to publish the message to
            message: The message to publish to that topic
            wait: Boolean variable to indicate if it should wait for a message
                  to be received before continuing

        returns:
            None

        raises:
            None
        '''

        # If wait is specified set self.waiting_for_message to true so that the
        # GUI will wait for a received message before continuing (e.g. if the 
        # user requests the settings, we will wait for the settings to come back
        # before letting the user do something
        self.waiting_for_message = wait
        print 'Sending message:{} to topic:{}'.format(message,topic)
        self.conn.publish(topic,message)

    def setupGUIElements(self):
        '''
        function:
            setupGUIElements: This function builds the 3 textboxes for the GUI

        args:
            None

        returns:
            None

        raises:
            None
        '''

        # Create all three textboxes and position them with a little space
        # between each one to accentuate each one
        self.firstTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE|wx.TE_WORDWRAP,pos=(0,0),size=(800,152))
        self.firstTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.secondTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE|wx.TE_WORDWRAP,pos=(0,155),size=(800,152))
        self.secondTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

        self.thirdTextBox = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE|wx.TE_WORDWRAP,pos=(0,310),size=(800,170))
        self.thirdTextBox.SetFont(wx.Font(30,wx.MODERN,wx.NORMAL,wx.NORMAL))

    def loadCallHistory(self):
        '''
        function:
            loadCallHistory: This function requests the call history and
                             displays it

        args:
            None

        returns:
            None

        raises:
            None
        ''' 

        # This global indicates that a call is currently incoming. Set it to
        # false since we are reloading the history
        global CALL_INC
        CALL_INC = False

        # Reset the points and reload the call history
        self.menu_items_list = ['{}\nSettings\n{}'.format(self.line_space,self.line_space)]
        self.menu_ptr = 1
        self.current_selected_text_box = 0
        self.current_top_ptr = 1
        self.using_settings = False
        self.end_of_call_history = False
        self.sendMessage('history_get','10:0',False)
	
        # highlight the currently selected menu item
        self.highlightBox(self.firstTextBox)

    def setupCallHistory(self):
	'''
	function:
	    setupCallHistory: function to request the call history from the backend
                         and dipslay them on the screen.

	args:
	    None

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
        # Pick the list to use so that we can update the correct values        
        list_to_use = self.setting_state_list if self.selecting_setting else self.settings_list if self.using_settings else self.menu_items_list

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
        '''
        function:
            formatMenuItem: function to format the name, number and
                            time when receiving data from the backend

        args:
            number: the number as a string to format as x (xxx) xxx - xxxx
            name: the name as a string which gets padded with spaces
            date: the date as a string which also gets padded with spaces

        returns:
            string: The returned string contains the formatted menu
                    item.

        raises:
            None
        '''

        # Reformat the number
        number = '        {} ({}) {} - {}      '.format(number[:1],number[1:4],number[4:7],number[-4:])
        
        # Get the number of spaces to pad and format the name
        num_pad_spaces = int((32 - len(name))/2)
        name = '{}{}{}'.format(num_pad_spaces*' ',name,num_pad_spaces*' ')

        # Get the number of spaces to pad and format the date
        # date is received like: 20181125T1656
        dateObj = datetime.strptime(time, "%Y%m%dT%H%M")
        dateStr = dateObj.strftime("%m/%d/%Y %I:%M %p")
        
        num_pad_spaces = int((32 - len(dateStr))/2)
        time = '{}{}{}'.format(num_pad_spaces*' ',dateStr,num_pad_spaces*' ')

        # Return the reformatted string
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

        # These global variables are used to pass the messages between the handler and here
        global CALL_INC
        
        # Get the event code
        code = event.GetKeyCode()

        # If the event is an up arrow key pressed...
        if self.key_by_ascii_dict[code] == 'up':
            # As long as we are not waiting for a message and there's no incoming call...
            if not CALL_INC and not self.waiting_for_message:
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
            # As long as we are not waiting for a message and there's no incoming call...
            if not CALL_INC and not self.waiting_for_message:
                # Get the list to use
                list_to_use = self.setting_state_list if self.selecting_setting else self.settings_list if self.using_settings else self.menu_items_list
                # Only do anything if we are not at the bottom of the list.
                # Increment the pointers based on where we are in the GUI
                if self.menu_ptr < len(list_to_use)-1:
                    if self.menu_ptr - 2 == self.current_top_ptr:
                        self.current_top_ptr+=1
                    if self.current_selected_text_box != 2:
                        self.current_selected_text_box+=1
                    self.menu_ptr+=1

                # If the user wants to go further, then request more call history
                elif not self.end_of_call_history and not self.waiting_for_message and not self.using_settings:
                    self.sendMessage('history_get','10:{}'.format(len(self.menu_items_list)-1),True)

                # Update the values in the text boxes
                self.setValues()

        # If the event is the user hitting enter (or check button)
        if self.key_by_ascii_dict[code] == 'enter':
            # If there is an incoming call...
            if CALL_INC:
                # Blacklist the incoming call and let the user know they blacklisted it
                self.sendMessage('call_blacklist',CALL_REC_MSG,False)
                self.thirdTextBox.SetValue('\nCaller Has Been Blocked!')
            # Otherwise, if the user selected "Settings"...
            elif self.menu_ptr == 0 and not self.using_settings:
                # Reset the pointers and request the settings
                self.using_settings = True
                self.menu_ptr = 0
                self.current_selected_text_box = 0
                self.current_top_ptr = 0
                self.end_of_settings_ptr = 1
                self.firstTextBox.SetValue('\nLoading Current Settings...')
                self.secondTextBox.SetValue('')
                self.thirdTextBox.SetValue('')
                self.sendMessage('settings_request_all', 'no', True)
            # Otherwise, if the user is selecting one of the setting states...
            elif self.selecting_setting:
                # If the user did not pick something that's not a setting state...
                if self.menu_ptr != 0 and self.setting_state_list[self.menu_ptr].strip() != 'End of List':
                    # Reset the pointers and tell the backend to save this setting
                    self.selecting_setting = False
                    self.sendMessage('setting_set', '{}:{}'.format(self.state_name,self.setting_state_list[self.menu_ptr].strip()), False)
                    self.menu_ptr = 0
                    self.current_selected_text_box = 0
                    self.current_top_ptr = 0

                    # Show the settings again
                    self.firstTextBox.SetValue(self.settings_list[self.menu_ptr])
                    self.secondTextBox.SetValue(self.settings_list[self.menu_ptr+1])
                    self.thirdTextBox.SetValue(self.settings_list[self.menu_ptr+2])
                    self.highlightBox(self.firstTextBox)

            # Otherwise, if the user is selecting one of the settings...
            elif self.using_settings:
                # If the user is not at the end of the settings list
                if self.settings_list[self.menu_ptr].strip() != 'End of Settings':
                    # Request the setting states from the backend, reset the pointers, and get
                    # ready to display them
                    self.sendMessage('setting_get', self.settings_list[self.menu_ptr].strip(),True)
                    self.selecting_setting = True
                    self.menu_ptr = 1
                    self.current_selected_text_box = 1
                    self.current_top_ptr = 0
                    self.firstTextBox.SetValue('\nLoading Selected Setting...')
                    self.secondTextBox.SetValue('')
                    self.thirdTextBox.SetValue('')
            
            elif self.menu_items_list[self.menu_ptr].strip() == 'End of Call History':
                return

            # else we are blacklisting a call from the history
            else:
                print 'self.menu_ptr={} self.current_top_ptr={} self.current_selected_text_box={}'.format(self.menu_ptr, self.current_top_ptr, self.current_selected_text_box)
                menuStr = self.menu_items_list[self.menu_ptr].split('\n')[0]
                nameStr = self.menu_items_list[self.menu_ptr].split('\n')[1]

                # ripped from https://stackoverflow.com/a/1451407
                all = string.maketrans('', '')
                nodigs = all.translate(all, string.digits)
                numToBlacklist = menuStr.translate(all, nodigs) + ':' + nameStr.replace(' ','')
                self.sendMessage('call_blacklist', numToBlacklist, False)
                self.menu_items_list[self.menu_ptr] = '{}\nCaller blacklisted!\n{}'.format(self.line_space, self.line_space)
                self.setValues()
                

        # If the user hits backspace (or cancel)
        if self.key_by_ascii_dict[code] == 'backspace':
            # If there is no incoming call and we are not waiting for a message...
            if not CALL_INC and not self.waiting_for_message:
                # If the user is picking a setting state...
                if self.selecting_setting:
                    # Reset the pointers and go back to settings
                    self.menu_ptr = 0
                    self.current_selected_text_box = 0
                    self.current_top_ptr = 0
                    self.selecting_setting = False
                    self.firstTextBox.SetValue(self.settings_list[0])
                    self.secondTextBox.SetValue(self.settings_list[1])
                    self.thirdTextBox.SetValue(self.settings_list[2])
                    self.highlightBox(self.firstTextBox)

                # Otherwise, if the user is selecting settings...
                elif self.using_settings:
                    # Get the call history again
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

