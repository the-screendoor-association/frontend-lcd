import wx
from datetime import datetime

class FrontEnd(wx.Frame):

    def __init__(self, parent, title):
        super(FrontEnd, self).__init__(parent,title=title, size=(800,480))
        self.Centre()
        self.setupGUIElements()
        self.loadCallHistory()

    def setupGUIElements(self):
        self.settingsBtn = wx.Button(self,label='Settings',pos=(0,0),size=(800,50))
        self.settingsBtn.SetFont(wx.Font(20,wx.DECORATIVE,wx.NORMAL,wx.NORMAL))
        
        self.historyList = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_CENTRE,pos=(0,50),size=(800,430))
        self.historyList.SetFont(wx.Font(15,wx.MODERN,wx.NORMAL,wx.NORMAL))

    def loadCallHistory(self):
        now = datetime.now()
        ampm = 'pm' if now.hour >= 12 else 'am'
        self.historyList.AppendText(now.strftime('%m/%d/%Y %I:%M:%S ') + ampm + ' ----  David Greeson  --- 1 (555) 555-5555\n')
        for i in range(1,17):
            date = datetime(2018,10,21,23-i,0,0)
            ampm = 'pm' if date.hour >= 12 else 'am'
            self.historyList.AppendText(date.strftime('%m/%d/%Y %I:%M:%S ') +  ampm + ' ----   Gantt Chart   --- 1 (555) 555-1234\n')

if __name__ == '__main__':
    app = wx.App()
    window = FrontEnd(None, title='Screen Door')
    window.Show()
    app.MainLoop()
