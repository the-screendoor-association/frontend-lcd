'''
 frontend.py
 User interface for ScreenDoorSDP
 Author: David Greeson
 Created: 10/22/18
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
	    __init__: constructor for the FrontEnd class. It calls the super()
		      constructor to build the GUI window, creates and places
		      the rest of the GUI elements, and loads the call history

	args:
	    parent: The parent object (using default)
	    title: The title which is passed in when creating the FrontEnd
		   object

	returns:
	    None

	raises:
	    None
	'''
        super(FrontEnd, self).__init__(parent,title=title, size=(800,480))
        self.Centre()
        self.setupGUIElements()
        self.loadCallHistory(17)

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
        self.settingsBtn = wx.Button(self,label='Settings',pos=(0,0),size=(800,50))
        self.settingsBtn.SetFont(wx.Font(20,wx.DECORATIVE,wx.NORMAL,wx.NORMAL))
        
        self.historyList = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,50),size=(800,430))
        self.historyList.SetFont(wx.Font(15,wx.MODERN,wx.NORMAL,wx.NORMAL))

    def loadCallHistory(self, num_calls=17):
	'''
	function:
	    loadCallHistory: function to request the call history from the
                             backend and display them on the screen.

	args:
	    num_calls: the number of calls to display on the call history

	returns:
	    None

	raises:
	    None
	'''
        now = datetime.now()
        ampm = 'pm' if now.hour >= 12 else 'am'
        self.historyList.AppendText(now.strftime('%m/%d/%Y %I:%M:%S ') + ampm + ' ----  David Greeson  --- 1 (555) 555-5555\n')
        for i in range(1,num_calls):
            date = datetime(2018,10,21,23-i,0,0)
            ampm = 'pm' if date.hour >= 12 else 'am'
            self.historyList.AppendText(date.strftime('%m/%d/%Y %I:%M:%S ') +  ampm + ' ----   Gantt Chart   --- 1 (555) 555-1234\n')

if __name__ == '__main__':
    app = wx.App()
    window = FrontEnd(None, title='Screen Door')
    window.Show()
    app.MainLoop()
