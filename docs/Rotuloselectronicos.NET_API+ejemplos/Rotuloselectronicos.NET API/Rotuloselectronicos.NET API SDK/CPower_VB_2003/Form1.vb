Public Class Form1
    Inherits System.Windows.Forms.Form
    Dim m_nPort As Byte  
    Dim m_nBaudrate As Integer 
    Dim m_nTimeout As Integer   
    Dim m_nCardID As Byte  

    Dim m_nCommType As Byte
    Dim m_nIPPort As Integer
    Dim m_dwIPAddr As Integer
    Dim m_dwIDCode As Integer

    Dim m_baudtbl() As Long = {115200, 57600, 38400, 19200, 9600, 4800, 2400}

#Region " Windows "

    Public Sub New()
        MyBase.New()

        InitializeComponent()


    End Sub

    Protected Overloads Overrides Sub Dispose(ByVal disposing As Boolean)
        If disposing Then
            If Not (components Is Nothing) Then
                components.Dispose()
            End If
        End If
        MyBase.Dispose(disposing)
    End Sub

    Private components As System.ComponentModel.IContainer


    Friend WithEvents Label1 As System.Windows.Forms.Label
    Friend WithEvents Label2 As System.Windows.Forms.Label
    Friend WithEvents Label3 As System.Windows.Forms.Label
    Friend WithEvents Label4 As System.Windows.Forms.Label
    Friend WithEvents Label5 As System.Windows.Forms.Label
    Friend WithEvents m_cmbPort As System.Windows.Forms.ComboBox
    Friend WithEvents m_cmbBaudrate As System.Windows.Forms.ComboBox
    Friend WithEvents m_cmbID As System.Windows.Forms.ComboBox
    Friend WithEvents btnSplitWnd As System.Windows.Forms.Button
    Friend WithEvents btnSendPicture As System.Windows.Forms.Button
    Friend WithEvents btnSendStaticText As System.Windows.Forms.Button
    Friend WithEvents btnSendClock As System.Windows.Forms.Button
    Friend WithEvents m_edtWidth As System.Windows.Forms.TextBox
    Friend WithEvents m_edtHeight As System.Windows.Forms.TextBox
    Friend WithEvents m_edtPicture As System.Windows.Forms.TextBox
    Friend WithEvents m_edtStaticText As System.Windows.Forms.TextBox
    Friend WithEvents btnSetTime As System.Windows.Forms.Button
    Friend WithEvents btnPlayOneProgram As System.Windows.Forms.Button
    Friend WithEvents m_edtSelProgram As System.Windows.Forms.TextBox
    Friend WithEvents Label6 As System.Windows.Forms.Label
    Friend WithEvents Label7 As System.Windows.Forms.Label
    Friend WithEvents Label8 As System.Windows.Forms.Label
    Friend WithEvents RadioBtnCom As System.Windows.Forms.RadioButton
    Friend WithEvents RadioBtnNetWork As System.Windows.Forms.RadioButton
    Friend WithEvents IPPort As System.Windows.Forms.TextBox
    Friend WithEvents IPAddr As System.Windows.Forms.TextBox
    Friend WithEvents IDCode As System.Windows.Forms.TextBox
    Friend WithEvents m_edtText1 As System.Windows.Forms.TextBox
    Friend WithEvents WndNo As System.Windows.Forms.ComboBox
    Friend WithEvents Label9 As System.Windows.Forms.Label
    Friend WithEvents GroupBox1 As System.Windows.Forms.GroupBox
    Friend WithEvents btnSendText As System.Windows.Forms.Button
    Friend WithEvents GroupBox2 As System.Windows.Forms.GroupBox
    Friend WithEvents MakeProgram As System.Windows.Forms.Button
    Friend WithEvents MakePlaybill As System.Windows.Forms.Button
    Friend WithEvents Upload As System.Windows.Forms.Button
    <System.Diagnostics.DebuggerStepThrough()> Private Sub InitializeComponent()
        Me.Label1 = New System.Windows.Forms.Label
        Me.m_cmbPort = New System.Windows.Forms.ComboBox
        Me.m_cmbBaudrate = New System.Windows.Forms.ComboBox
        Me.Label2 = New System.Windows.Forms.Label
        Me.m_cmbID = New System.Windows.Forms.ComboBox
        Me.Label3 = New System.Windows.Forms.Label
        Me.btnSplitWnd = New System.Windows.Forms.Button
        Me.btnSendText = New System.Windows.Forms.Button
        Me.btnSendPicture = New System.Windows.Forms.Button
        Me.btnSendStaticText = New System.Windows.Forms.Button
        Me.btnSendClock = New System.Windows.Forms.Button
        Me.Label4 = New System.Windows.Forms.Label
        Me.m_edtWidth = New System.Windows.Forms.TextBox
        Me.Label5 = New System.Windows.Forms.Label
        Me.m_edtHeight = New System.Windows.Forms.TextBox
        Me.m_edtText1 = New System.Windows.Forms.TextBox
        Me.m_edtPicture = New System.Windows.Forms.TextBox
        Me.m_edtStaticText = New System.Windows.Forms.TextBox
        Me.btnSetTime = New System.Windows.Forms.Button
        Me.btnPlayOneProgram = New System.Windows.Forms.Button
        Me.m_edtSelProgram = New System.Windows.Forms.TextBox
        Me.RadioBtnCom = New System.Windows.Forms.RadioButton
        Me.RadioBtnNetWork = New System.Windows.Forms.RadioButton
        Me.Label6 = New System.Windows.Forms.Label
        Me.Label7 = New System.Windows.Forms.Label
        Me.Label8 = New System.Windows.Forms.Label
        Me.IPPort = New System.Windows.Forms.TextBox
        Me.IPAddr = New System.Windows.Forms.TextBox
        Me.IDCode = New System.Windows.Forms.TextBox
        Me.WndNo = New System.Windows.Forms.ComboBox
        Me.Label9 = New System.Windows.Forms.Label
        Me.GroupBox1 = New System.Windows.Forms.GroupBox
        Me.GroupBox2 = New System.Windows.Forms.GroupBox
        Me.MakeProgram = New System.Windows.Forms.Button
        Me.MakePlaybill = New System.Windows.Forms.Button
        Me.Upload = New System.Windows.Forms.Button
        Me.GroupBox1.SuspendLayout()
        Me.GroupBox2.SuspendLayout()
        Me.SuspendLayout()
        '
        'Label1
        '
        Me.Label1.Location = New System.Drawing.Point(120, 24)
        Me.Label1.Name = "Label1"
        Me.Label1.Size = New System.Drawing.Size(56, 16)
        Me.Label1.TabIndex = 0
        Me.Label1.Text = "COM Port"
        '
        'm_cmbPort
        '
        Me.m_cmbPort.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList
        Me.m_cmbPort.Location = New System.Drawing.Point(184, 24)
        Me.m_cmbPort.Name = "m_cmbPort"
        Me.m_cmbPort.Size = New System.Drawing.Size(96, 20)
        Me.m_cmbPort.TabIndex = 1
        '
        'm_cmbBaudrate
        '
        Me.m_cmbBaudrate.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList
        Me.m_cmbBaudrate.Items.AddRange(New Object() {"115200", "57600", "38400", "19200", "9600", "4800", "2400"})
        Me.m_cmbBaudrate.Location = New System.Drawing.Point(368, 24)
        Me.m_cmbBaudrate.Name = "m_cmbBaudrate"
        Me.m_cmbBaudrate.Size = New System.Drawing.Size(96, 20)
        Me.m_cmbBaudrate.TabIndex = 1
        '
        'Label2
        '
        Me.Label2.Location = New System.Drawing.Point(296, 24)
        Me.Label2.Name = "Label2"
        Me.Label2.Size = New System.Drawing.Size(64, 16)
        Me.Label2.TabIndex = 0
        Me.Label2.Text = "Baudrate"
        '
        'm_cmbID
        '
        Me.m_cmbID.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList
        Me.m_cmbID.Location = New System.Drawing.Point(584, 24)
        Me.m_cmbID.Name = "m_cmbID"
        Me.m_cmbID.Size = New System.Drawing.Size(96, 20)
        Me.m_cmbID.TabIndex = 1
        '
        'Label3
        '
        Me.Label3.Location = New System.Drawing.Point(488, 24)
        Me.Label3.Name = "Label3"
        Me.Label3.Size = New System.Drawing.Size(88, 16)
        Me.Label3.TabIndex = 0
        Me.Label3.Text = "Controller ID"
        '
        'btnSplitWnd
        '
        Me.btnSplitWnd.Location = New System.Drawing.Point(8, 120)
        Me.btnSplitWnd.Name = "btnSplitWnd"
        Me.btnSplitWnd.Size = New System.Drawing.Size(112, 23)
        Me.btnSplitWnd.TabIndex = 2
        Me.btnSplitWnd.Text = "Make two window"
        '
        'btnSendText
        '
        Me.btnSendText.Location = New System.Drawing.Point(8, 160)
        Me.btnSendText.Name = "btnSendText"
        Me.btnSendText.Size = New System.Drawing.Size(112, 23)
        Me.btnSendText.TabIndex = 2
        Me.btnSendText.Text = "Send Text"
        '
        'btnSendPicture
        '
        Me.btnSendPicture.Location = New System.Drawing.Point(8, 200)
        Me.btnSendPicture.Name = "btnSendPicture"
        Me.btnSendPicture.Size = New System.Drawing.Size(112, 23)
        Me.btnSendPicture.TabIndex = 2
        Me.btnSendPicture.Text = "Send Picture"
        '
        'btnSendStaticText
        '
        Me.btnSendStaticText.Location = New System.Drawing.Point(8, 240)
        Me.btnSendStaticText.Name = "btnSendStaticText"
        Me.btnSendStaticText.Size = New System.Drawing.Size(112, 23)
        Me.btnSendStaticText.TabIndex = 2
        Me.btnSendStaticText.Text = "Send Static Text"
        '
        'btnSendClock
        '
        Me.btnSendClock.Location = New System.Drawing.Point(8, 280)
        Me.btnSendClock.Name = "btnSendClock"
        Me.btnSendClock.Size = New System.Drawing.Size(112, 23)
        Me.btnSendClock.TabIndex = 2
        Me.btnSendClock.Text = "Send Clock"
        '
        'Label4
        '
        Me.Label4.Location = New System.Drawing.Point(136, 120)
        Me.Label4.Name = "Label4"
        Me.Label4.Size = New System.Drawing.Size(40, 16)
        Me.Label4.TabIndex = 0
        Me.Label4.Text = "Width"
        '
        'm_edtWidth
        '
        Me.m_edtWidth.Location = New System.Drawing.Point(176, 120)
        Me.m_edtWidth.Name = "m_edtWidth"
        Me.m_edtWidth.Size = New System.Drawing.Size(48, 21)
        Me.m_edtWidth.TabIndex = 3
        Me.m_edtWidth.Text = "64"
        '
        'Label5
        '
        Me.Label5.Location = New System.Drawing.Point(232, 120)
        Me.Label5.Name = "Label5"
        Me.Label5.Size = New System.Drawing.Size(48, 16)
        Me.Label5.TabIndex = 0
        Me.Label5.Text = "Height"
        '
        'm_edtHeight
        '
        Me.m_edtHeight.Location = New System.Drawing.Point(280, 120)
        Me.m_edtHeight.Name = "m_edtHeight"
        Me.m_edtHeight.Size = New System.Drawing.Size(48, 21)
        Me.m_edtHeight.TabIndex = 3
        Me.m_edtHeight.Text = "32"
        '
        'm_edtText1
        '
        Me.m_edtText1.AcceptsReturn = True
        Me.m_edtText1.Location = New System.Drawing.Point(144, 152)
        Me.m_edtText1.Multiline = True
        Me.m_edtText1.Name = "m_edtText1"
        Me.m_edtText1.Size = New System.Drawing.Size(184, 40)
        Me.m_edtText1.TabIndex = 3
        Me.m_edtText1.Text = "texto"
        '
        'm_edtPicture
        '
        Me.m_edtPicture.Location = New System.Drawing.Point(144, 200)
        Me.m_edtPicture.Name = "m_edtPicture"
        Me.m_edtPicture.Size = New System.Drawing.Size(184, 21)
        Me.m_edtPicture.TabIndex = 3
        Me.m_edtPicture.Text = "test.bmp"
        '
        'm_edtStaticText
        '
        Me.m_edtStaticText.Location = New System.Drawing.Point(144, 240)
        Me.m_edtStaticText.Name = "m_edtStaticText"
        Me.m_edtStaticText.Size = New System.Drawing.Size(184, 21)
        Me.m_edtStaticText.TabIndex = 3
        Me.m_edtStaticText.Text = "Welcome to !"
        '
        'btnSetTime
        '
        Me.btnSetTime.Location = New System.Drawing.Point(144, 280)
        Me.btnSetTime.Name = "btnSetTime"
        Me.btnSetTime.Size = New System.Drawing.Size(112, 23)
        Me.btnSetTime.TabIndex = 2
        Me.btnSetTime.Text = "Set Time"
        '
        'btnPlayOneProgram
        '
        Me.btnPlayOneProgram.Location = New System.Drawing.Point(360, 152)
        Me.btnPlayOneProgram.Name = "btnPlayOneProgram"
        Me.btnPlayOneProgram.Size = New System.Drawing.Size(112, 23)
        Me.btnPlayOneProgram.TabIndex = 2
        Me.btnPlayOneProgram.Text = "Play One Program"
        '
        'm_edtSelProgram
        '
        Me.m_edtSelProgram.Location = New System.Drawing.Point(504, 152)
        Me.m_edtSelProgram.Name = "m_edtSelProgram"
        Me.m_edtSelProgram.Size = New System.Drawing.Size(72, 21)
        Me.m_edtSelProgram.TabIndex = 3
        Me.m_edtSelProgram.Text = "1"
        '
        'RadioBtnCom
        '
        Me.RadioBtnCom.Location = New System.Drawing.Point(16, 24)
        Me.RadioBtnCom.Name = "RadioBtnCom"
        Me.RadioBtnCom.Size = New System.Drawing.Size(80, 16)
        Me.RadioBtnCom.TabIndex = 4
        Me.RadioBtnCom.Text = "RS232/485"
        '
        'RadioBtnNetWork
        '
        Me.RadioBtnNetWork.Location = New System.Drawing.Point(16, 64)
        Me.RadioBtnNetWork.Name = "RadioBtnNetWork"
        Me.RadioBtnNetWork.Size = New System.Drawing.Size(80, 16)
        Me.RadioBtnNetWork.TabIndex = 4
        Me.RadioBtnNetWork.Text = "NetWork"
        '
        'Label6
        '
        Me.Label6.Location = New System.Drawing.Point(488, 64)
        Me.Label6.Name = "Label6"
        Me.Label6.Size = New System.Drawing.Size(88, 16)
        Me.Label6.TabIndex = 0
        Me.Label6.Text = "ID Code"
        '
        'Label7
        '
        Me.Label7.Location = New System.Drawing.Point(296, 64)
        Me.Label7.Name = "Label7"
        Me.Label7.Size = New System.Drawing.Size(64, 16)
        Me.Label7.TabIndex = 0
        Me.Label7.Text = "IP Port"
        '
        'Label8
        '
        Me.Label8.Location = New System.Drawing.Point(120, 64)
        Me.Label8.Name = "Label8"
        Me.Label8.Size = New System.Drawing.Size(56, 16)
        Me.Label8.TabIndex = 0
        Me.Label8.Text = "IP Addr"
        '
        'IPPort
        '
        Me.IPPort.Location = New System.Drawing.Point(368, 64)
        Me.IPPort.Name = "IPPort"
        Me.IPPort.Size = New System.Drawing.Size(96, 21)
        Me.IPPort.TabIndex = 3
        Me.IPPort.Text = "5200"
        '
        'IPAddr
        '
        Me.IPAddr.Location = New System.Drawing.Point(184, 64)
        Me.IPAddr.Name = "IPAddr"
        Me.IPAddr.Size = New System.Drawing.Size(96, 21)
        Me.IPAddr.TabIndex = 5
        Me.IPAddr.Text = "192.168.1.100"
        '
        'IDCode
        '
        Me.IDCode.Location = New System.Drawing.Point(584, 64)
        Me.IDCode.Name = "IDCode"
        Me.IDCode.Size = New System.Drawing.Size(96, 21)
        Me.IDCode.TabIndex = 5
        Me.IDCode.Text = "255.255.255.255"
        '
        'WndNo
        '
        Me.WndNo.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList
        Me.WndNo.Items.AddRange(New Object() {"0", "1"})
        Me.WndNo.Location = New System.Drawing.Point(504, 120)
        Me.WndNo.Name = "WndNo"
        Me.WndNo.Size = New System.Drawing.Size(72, 20)
        Me.WndNo.TabIndex = 7
        '
        'Label9
        '
        Me.Label9.Location = New System.Drawing.Point(360, 120)
        Me.Label9.Name = "Label9"
        Me.Label9.Size = New System.Drawing.Size(120, 16)
        Me.Label9.TabIndex = 6
        Me.Label9.Text = "Select send window"
        '
        'GroupBox1
        '
        Me.GroupBox1.Controls.Add(Me.RadioBtnCom)
        Me.GroupBox1.Controls.Add(Me.RadioBtnNetWork)
        Me.GroupBox1.Controls.Add(Me.m_cmbPort)
        Me.GroupBox1.Controls.Add(Me.Label6)
        Me.GroupBox1.Controls.Add(Me.Label7)
        Me.GroupBox1.Controls.Add(Me.m_cmbBaudrate)
        Me.GroupBox1.Controls.Add(Me.Label1)
        Me.GroupBox1.Controls.Add(Me.Label2)
        Me.GroupBox1.Controls.Add(Me.m_cmbID)
        Me.GroupBox1.Controls.Add(Me.Label3)
        Me.GroupBox1.Controls.Add(Me.IPAddr)
        Me.GroupBox1.Controls.Add(Me.IDCode)
        Me.GroupBox1.Controls.Add(Me.Label8)
        Me.GroupBox1.Controls.Add(Me.IPPort)
        Me.GroupBox1.Location = New System.Drawing.Point(8, 8)
        Me.GroupBox1.Name = "GroupBox1"
        Me.GroupBox1.Size = New System.Drawing.Size(696, 96)
        Me.GroupBox1.TabIndex = 8
        Me.GroupBox1.TabStop = False
        '
        'GroupBox2
        '
        Me.GroupBox2.Controls.Add(Me.MakeProgram)
        Me.GroupBox2.Controls.Add(Me.MakePlaybill)
        Me.GroupBox2.Controls.Add(Me.Upload)
        Me.GroupBox2.Location = New System.Drawing.Point(360, 192)
        Me.GroupBox2.Name = "GroupBox2"
        Me.GroupBox2.Size = New System.Drawing.Size(320, 120)
        Me.GroupBox2.TabIndex = 9
        Me.GroupBox2.TabStop = False
        Me.GroupBox2.Text = "Make program/playbill and upload"
        '
        'MakeProgram
        '
        Me.MakeProgram.Location = New System.Drawing.Point(80, 24)
        Me.MakeProgram.Name = "MakeProgram"
        Me.MakeProgram.Size = New System.Drawing.Size(160, 23)
        Me.MakeProgram.TabIndex = 0
        Me.MakeProgram.Text = "Make program"
        '
        'MakePlaybill
        '
        Me.MakePlaybill.Location = New System.Drawing.Point(80, 56)
        Me.MakePlaybill.Name = "MakePlaybill"
        Me.MakePlaybill.Size = New System.Drawing.Size(160, 23)
        Me.MakePlaybill.TabIndex = 0
        Me.MakePlaybill.Text = "Make playbill"
        '
        'Upload
        '
        Me.Upload.Location = New System.Drawing.Point(80, 88)
        Me.Upload.Name = "Upload"
        Me.Upload.Size = New System.Drawing.Size(160, 23)
        Me.Upload.TabIndex = 0
        Me.Upload.Text = "Upload and restart App"
        '
        'Form1
        '
        Me.AutoScaleBaseSize = New System.Drawing.Size(6, 14)
        Me.ClientSize = New System.Drawing.Size(712, 326)
        Me.Controls.Add(Me.GroupBox2)
        Me.Controls.Add(Me.GroupBox1)
        Me.Controls.Add(Me.WndNo)
        Me.Controls.Add(Me.Label9)
        Me.Controls.Add(Me.m_edtWidth)
        Me.Controls.Add(Me.btnSplitWnd)
        Me.Controls.Add(Me.btnSendText)
        Me.Controls.Add(Me.btnSendPicture)
        Me.Controls.Add(Me.btnSendStaticText)
        Me.Controls.Add(Me.btnSendClock)
        Me.Controls.Add(Me.Label4)
        Me.Controls.Add(Me.Label5)
        Me.Controls.Add(Me.m_edtHeight)
        Me.Controls.Add(Me.m_edtText1)
        Me.Controls.Add(Me.m_edtPicture)
        Me.Controls.Add(Me.m_edtStaticText)
        Me.Controls.Add(Me.btnSetTime)
        Me.Controls.Add(Me.m_edtSelProgram)
        Me.Controls.Add(Me.btnPlayOneProgram)
        Me.Name = "Form1"
        Me.Text = "C-Power Demo"
        Me.GroupBox1.ResumeLayout(False)
        Me.GroupBox2.ResumeLayout(False)
        Me.ResumeLayout(False)

    End Sub

#End Region


    Private Declare Function CP5200_Playbill_Create Lib "CP5200.dll" (ByVal width As Integer, ByVal height As Integer, ByVal color As Byte) As Integer
    Private Declare Function CP5200_Playbill_Destroy Lib "CP5200.dll" (ByVal hObj As Integer) As Integer
    Private Declare Function CP5200_Playbill_AddFile Lib "CP5200.dll" (ByVal hObj As Integer, ByVal pText As String) As Integer
    Private Declare Function CP5200_Playbill_SaveToFile Lib "CP5200.dll" (ByVal hObj As Integer, ByVal pText As String) As Integer

    Private Declare Function CP5200_Program_Create Lib "CP5200.dll" (ByVal width As Integer, ByVal height As Integer, ByVal color As Byte) As Integer
    Private Declare Function CP5200_Program_Destroy Lib "CP5200.dll" (ByVal hObj As Integer) As Integer
    Private Declare Function CP5200_Program_SetProperty Lib "CP5200.dll" (ByVal hObj As Integer, ByVal nPropertyValue As Integer, ByVal nPropertyID As Integer) As Integer
    Private Declare Function CP5200_Program_AddPlayWindow Lib "CP5200.dll" (ByVal hObj As Integer, ByVal x As Integer, ByVal y As Integer, ByVal cx As Integer, ByVal cy As Integer) As Integer
    Private Declare Function CP5200_Program_SetWindowProperty Lib "CP5200.dll" (ByVal hObj As Integer, ByVal nWndNo As Integer, ByVal nPropertyValue As Integer, ByVal nPropertyID As Integer) As Integer
    Private Declare Function CP5200_Program_AddText Lib "CP5200.dll" (ByVal hObj As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal nFontSize As Integer, ByVal crColor As Integer, ByVal nEffect As Integer, ByVal nSpeed As Integer, ByVal nStay As Integer) As Integer
    Private Declare Function CP5200_Program_AddPicture Lib "CP5200.dll" (ByVal hObj As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal nMode As Integer, ByVal nEffect As Integer, ByVal nSpeed As Integer, ByVal nStay As Integer, ByVal nCompress As Integer) As Integer
    Private Declare Function CP5200_Program_SaveToFile Lib "CP5200.dll" (ByVal hObj As Integer, ByVal pText As String) As Integer


    'Rs232/485
    Private Declare Function CP5200_RS232_InitEx Lib "CP5200.dll" (ByVal fName As String, ByVal nBaudrate As Integer, ByVal nTimeout As Integer) As Integer
    Private Declare Function CP5200_RS232_Open Lib "CP5200.dll" () As Integer
    Private Declare Function CP5200_RS232_Close Lib "CP5200.dll" () As Integer
    Private Declare Function CP5200_RS232_WriteEx Lib "CP5200.dll" (ByVal pBuf As Integer, ByVal nLength As Integer) As Integer
    Private Declare Function CP5200_RS232_ReadEx Lib "CP5200.dll" (ByVal pBuf As Integer, ByVal nBufSize As Integer) As Integer
    Private Declare Function CP5200_RS232_PlaySelectedPrg Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pSelected() As Short, ByVal nSelCnt As Integer, ByVal nOption As Integer) As Integer
    Private Declare Function CP5200_RS232_SendText Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal crColor As Integer, ByVal nFontSize As Integer, ByVal nSpeed As Integer, ByVal nEffect As Integer, ByVal nStayTime As Integer, ByVal nAlignment As Integer) As Integer
    Private Declare Function CP5200_RS232_SendPicture Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal nPosX As Integer, ByVal nPosY As Integer, ByVal nCx As Integer, ByVal nCy As Integer, ByVal pPictureFile As String, ByVal nSpeed As Integer, ByVal nEffect As Integer, ByVal nStayTime As Integer, ByVal nPictRef As Integer) As Integer
    Private Declare Function CP5200_RS232_SendStatic Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal crColor As Integer, ByVal nFontSize As Integer, ByVal nAlignment As Integer, ByVal x As Integer, ByVal y As Integer, ByVal cx As Integer, ByVal cy As Integer) As Integer
    Private Declare Function CP5200_RS232_SendClock Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWinNo As Integer, ByVal nStayTime As Integer, ByVal nCalendar As Integer, ByVal nFormat As Integer, ByVal nContent As Integer, ByVal nFont As Integer, ByVal nRed As Integer, ByVal nGreen As Integer, ByVal nBlue As Integer, ByVal pTxt As String) As Integer
    Private Declare Function CP5200_RS232_SetTime Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pInfo() As Byte) As Integer
    Private Declare Function CP5200_RS232_SplitScreen Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nScrWidth As Integer, ByVal ScrHeight As Integer, ByVal nWndCnt As Integer, ByVal pWndRects() As Integer) As Integer
    Private Declare Function CP5200_RS232_UploadFile Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pSourceFilename As String, ByVal pTargetFilename As String) As Integer
    Private Declare Function CP5200_RS232_RestartApp Lib "CP5200.dll" (ByVal nCardID As Integer) As Integer


    'NetWork
    Private Declare Function CP5200_Net_Init Lib "CP5200.dll" (ByVal dwIP As Integer, ByVal nIPPort As Integer, ByVal dwIDCode As Integer, ByVal nTimeout As Integer) As Integer
    Private Declare Function CP5200_Net_Connect Lib "CP5200.dll" () As Integer
    Private Declare Function CP5200_Net_Disconnect Lib "CP5200.dll" () As Integer
    Private Declare Function CP5200_Net_Write Lib "CP5200.dll" (ByVal pBuf As Integer, ByVal nLength As Integer) As Integer
    Private Declare Function CP5200_Net_Read Lib "CP5200.dll" (ByVal pBuf As Integer, ByVal nBufSize As Integer) As Integer
    Private Declare Function CP5200_Net_PlaySelectedPrg Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pSelected() As Short, ByVal nSelCnt As Integer, ByVal nOption As Integer) As Integer
    Private Declare Function CP5200_Net_SendText Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal crColor As Integer, ByVal nFontSize As Integer, ByVal nSpeed As Integer, ByVal nEffect As Integer, ByVal nStayTime As Integer, ByVal nAlignment As Integer) As Integer
    Private Declare Function CP5200_Net_SendPicture Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal nPosX As Integer, ByVal nPosY As Integer, ByVal nCx As Integer, ByVal nCy As Integer, ByVal pPictureFile As String, ByVal nSpeed As Integer, ByVal nEffect As Integer, ByVal nStayTime As Integer, ByVal nPictRef As Integer) As Integer
    Private Declare Function CP5200_Net_SendStatic Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWndNo As Integer, ByVal pText As String, ByVal crColor As Integer, ByVal nFontSize As Integer, ByVal nAlignment As Integer, ByVal x As Integer, ByVal y As Integer, ByVal cx As Integer, ByVal cy As Integer) As Integer
    Private Declare Function CP5200_Net_SendClock Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nWinNo As Integer, ByVal nStayTime As Integer, ByVal nCalendar As Integer, ByVal nFormat As Integer, ByVal nContent As Integer, ByVal nFont As Integer, ByVal nRed As Integer, ByVal nGreen As Integer, ByVal nBlue As Integer, ByVal pTxt As String) As Integer
    Private Declare Function CP5200_Net_SetTime Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pInfo() As Byte) As Integer
    Private Declare Function CP5200_Net_SplitScreen Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal nScrWidth As Integer, ByVal ScrHeight As Integer, ByVal nWndCnt As Integer, ByVal pWndRects() As Integer) As Integer
    Private Declare Function CP5200_Net_UploadFile Lib "CP5200.dll" (ByVal nCardID As Integer, ByVal pSourceFilename As String, ByVal pTargetFilename As String) As Integer
    Private Declare Function CP5200_Net_RestartApp Lib "CP5200.dll" (ByVal nCardID As Integer) As Integer



    Private Function CountIF(ByRef lzExpr As String, ByRef nChar As String) As Object
        Dim X, iCount As Short
        Dim sByte() As Byte
        sByte = System.Text.UnicodeEncoding.Unicode.GetBytes(lzExpr)
        For X = LBound(sByte) To UBound(sByte)
            If sByte(X) = Asc(nChar) Then iCount = iCount + 1
        Next
        X = 0 : Erase sByte
        CountIF = iCount
        iCount = 0
    End Function

    Private Function MAKEIPADDRESS(ByVal b1 As Byte, ByVal b2 As Byte, ByVal b3 As Byte, ByVal b4 As Byte) As Integer
        MAKEIPADDRESS = (CShort(b1 And &H7FS) * &H1000000 Or (b1 And &H80S) <> 0 And &H80000000) Or (b2 * &H10000) Or (b3 * &H100) Or (b4)
    End Function

    Private Function GetIP(ByVal Value As String) As Integer
        If CountIF(Value, ".") < 3 Then
            MessageBox.Show("IP address format error!")
            GetIP = 0
            Return 0
        Else
            Dim mByte(3) As Byte
            Dim mInt(3) As Integer
            Dim i As Integer
            Dim vIp As Object

            vIp = Split(Value, ".") 
            For i = 0 To 3
                mInt(i) = vIp(3 - i)
                If mInt(i) > 255 Or mInt(i) < 0 Then
                    Erase vIp
                    MessageBox.Show("IP address format error!")
                    GetIP = 0
                    Return 0
                Else
                    mByte(i) = mInt(i)
                End If
            Next i
            Erase vIp
            GetIP = MAKEIPADDRESS(mByte(3), mByte(2), mByte(1), mByte(0))
        End If
    End Function

    Private Function InitComm() As Integer
        Dim nRet As Integer = 0
        If m_nCommType = 0 Then
            Dim strPort As String
            strPort = "COM" + Format("%d", m_nPort)
            CP5200_RS232_InitEx(strPort, m_nBaudrate, m_nTimeout)
            nRet = 1
        Else
            m_dwIPAddr = GetIP(IPAddr.Text)
            If m_dwIPAddr <> 0 Then
                m_dwIDCode = GetIP(IDCode.Text)
                If m_dwIDCode <> 0 Then
                    CP5200_Net_Init(m_dwIPAddr, m_nIPPort, m_dwIDCode, m_nTimeout)
                    nRet = 1
                End If
            End If
        End If
        InitComm = nRet
        Return nRet
    End Function

    Private Sub GetSplitWnd(ByRef rcWins() As Integer)
        rcWins(0) = 0
        rcWins(1) = 0
        rcWins(2) = m_edtWidth.Text / 2
        rcWins(3) = m_edtHeight.Text
        rcWins(4) = m_edtWidth.Text / 2
        rcWins(5) = 0
        rcWins(6) = m_edtWidth.Text
        rcWins(7) = m_edtHeight.Text
    End Sub

    Private Sub Form1_Load(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MyBase.Load
        Dim strTemp As String
        Dim i As Integer
        For i = 1 To 16
            strTemp = "COM" + CStr(i)
            m_cmbPort.Items.Add(strTemp)
        Next i

        For i = 1 To 20
            strTemp = Format("%d", i)
            m_cmbID.Items.Add(strTemp)
        Next i

        m_nPort = 1
        m_nBaudrate = 115200
        m_nTimeout = 600
        m_nCardID = 1
        m_edtWidth.Text = 64
        m_edtHeight.Text = 32

        m_nCommType = 0
        m_nIPPort = 5200
        m_dwIPAddr = -1062731411
        m_dwIDCode = -1


        IPPort.Text = Format("%d", m_nIPPort)
        m_cmbID.SelectedIndex = m_nCardID - 1
        m_cmbPort.SelectedIndex = m_nPort - 1
        WndNo.SelectedIndex = 0

        For i = 0 To 5
            If m_nBaudrate = m_baudtbl(i) Then
                m_cmbBaudrate.SelectedIndex = i
            End If
        Next i

        If m_nCommType = 0 Then
            RadioBtnCom.Checked = True
            RadioBtnNetWork.Checked = False
        Else
            RadioBtnCom.Checked = False
            RadioBtnNetWork.Checked = True
        End If
    End Sub

    Private Sub m_cmbPort_SelectedIndexChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles m_cmbPort.SelectedIndexChanged
        m_nPort = m_cmbPort.SelectedIndex + 1
    End Sub

    Private Sub m_cmbBaudrate_SelectedIndexChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles m_cmbBaudrate.SelectedIndexChanged
        m_nBaudrate = m_baudtbl(m_cmbBaudrate.SelectedIndex)
    End Sub

    Private Sub m_cmbID_SelectedIndexChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles m_cmbID.SelectedIndexChanged
        m_nCardID = m_cmbID.SelectedIndex + 1
    End Sub

    Private Sub btnSplitWnd_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSplitWnd.Click
        Dim ret As Integer
        Dim nWndRect(7) As Integer
        GetSplitWnd(nWndRect)

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SplitScreen(m_nCardID, m_edtWidth.Text, m_edtHeight.Text, 2, nWndRect)
            Else
                ret = CP5200_Net_SplitScreen(m_nCardID, m_edtWidth.Text, m_edtHeight.Text, 2, nWndRect)
            End If

            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If

    End Sub

    Private Sub btnSendText1_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSendText.Click
        Dim ret As Integer
        Dim text As String
        text = m_edtText1.Text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendText(m_nCardID, WndNo.SelectedIndex, text, RGB(255, 0, 0), 16, 3, 0, 3, 5)
            Else
                ret = CP5200_Net_SendText(m_nCardID, WndNo.SelectedIndex, text, RGB(255, 0, 0), 16, 3, 0, 3, 5)
            End If


            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If

    End Sub
    Private Sub btnSendPicture_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSendPicture.Click
        Dim ret As Integer
        Dim text As String
        Dim nWndRect(7) As Integer
        GetSplitWnd(nWndRect)
        text = m_edtPicture.Text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendPicture(m_nCardID, WndNo.SelectedIndex, 0, 0, nWndRect(2 + WndNo.SelectedIndex * 4) - nWndRect(0 + WndNo.SelectedIndex * 4), nWndRect(3 + WndNo.SelectedIndex * 4) - nWndRect(1 + WndNo.SelectedIndex * 4), text, 1, 0, 3, 0)
            Else
                ret = CP5200_Net_SendPicture(m_nCardID, WndNo.SelectedIndex, 0, 0, nWndRect(2 + WndNo.SelectedIndex * 4) - nWndRect(0 + WndNo.SelectedIndex * 4), nWndRect(3 + WndNo.SelectedIndex * 4) - nWndRect(1 + WndNo.SelectedIndex * 4), text, 1, 0, 3, 0)
            End If

            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If
    End Sub

    Private Sub btnSendStaticText_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSendStaticText.Click
        Dim ret As Integer
        Dim text As String
        Dim nWndRect(7) As Integer
        GetSplitWnd(nWndRect)
        text = m_edtStaticText.Text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendStatic(m_nCardID, WndNo.SelectedIndex, text, RGB(255, 0, 0), 16, 0, 0, 0, nWndRect(2 + WndNo.SelectedIndex * 4) - nWndRect(0 + WndNo.SelectedIndex * 4), nWndRect(3 + WndNo.SelectedIndex * 4) - nWndRect(1 + WndNo.SelectedIndex * 4))
            Else
                ret = CP5200_Net_SendStatic(m_nCardID, WndNo.SelectedIndex, text, RGB(255, 0, 0), 16, 0, 0, 0, nWndRect(2 + WndNo.SelectedIndex * 4) - nWndRect(0 + WndNo.SelectedIndex * 4), nWndRect(3 + WndNo.SelectedIndex * 4) - nWndRect(1 + WndNo.SelectedIndex * 4))
            End If


            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If
    End Sub

    Private Sub btnSendClock_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSendClock.Click
        Dim ret As Integer
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendClock(m_nCardID, WndNo.SelectedIndex, 3, 0, 7, 7, 1, 255, 255, 255, "Date")
            Else
                ret = CP5200_Net_SendClock(m_nCardID, WndNo.SelectedIndex, 3, 0, 7, 7, 1, 255, 255, 255, "Date")
            End If

            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If
    End Sub

    Private Sub btnSetTime_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnSetTime.Click
        Dim ret As Integer
        Dim curTime As Date
        Dim byTime(6) As Byte

        curTime = DateTime.Now
        byTime(0) = curTime.Second
        byTime(1) = curTime.Minute
        byTime(2) = curTime.Hour
        byTime(3) = curTime.DayOfWeek
        byTime(4) = curTime.Day
        byTime(5) = curTime.Month
        byTime(6) = curTime.Year - 2000

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SetTime(m_nCardID, byTime)
            Else
                ret = CP5200_Net_SetTime(m_nCardID, byTime)
            End If

            If ret = 1 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If
    End Sub

    Private Sub btnPlayOneProgram_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles btnPlayOneProgram.Click
        Dim ret As Integer
        Dim prg As Integer
        Dim strPrg(255) As Short

        prg = m_edtSelProgram.Text
        If prg < 0 Then
            prg = 0
        End If
        strPrg(0) = prg
        strPrg(1) = 0

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_PlaySelectedPrg(m_nCardID, strPrg, 1, 0)
            Else
                ret = CP5200_Net_PlaySelectedPrg(m_nCardID, strPrg, 1, 0)
            End If

            If ret >= 0 Then
                MessageBox.Show("Successful")
            Else
                MessageBox.Show("Fail")
            End If
        End If
    End Sub


    Private Sub EnableCtrl()
        Dim bTure As Boolean = True
        If m_nCommType = 0 Then
            bTure = False
        End If

        m_cmbPort.Enabled = Not bTure
        m_cmbBaudrate.Enabled = Not bTure

        IPAddr.Enabled = bTure
        IPPort.Enabled = bTure
        IDCode.Enabled = bTure
    End Sub

    Private Sub RadioButton1_CheckedChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles RadioBtnCom.CheckedChanged
        m_nCommType = 0
        EnableCtrl()
    End Sub

    Private Sub RadioButton2_CheckedChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles RadioBtnNetWork.CheckedChanged
        m_nCommType = 1
        EnableCtrl()
    End Sub

    Private Sub IPPort_TextChanged(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles IPPort.TextChanged
        m_nIPPort = IPPort.Text
    End Sub

    Private Function GetProgramFileName() As String
        Dim strName As String
        strName = Format(m_nCardID, "0000") & "0000.lpb"
        Return strName
    End Function

    Private Function GetPlaybillFileName() As String
        Dim strName As String = "playbill.lpp"
        Return strName
    End Function

    Private Sub MakeProgram_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MakeProgram.Click
        Dim bRet As Boolean = False
        Dim nWndRect(7) As Integer
        Dim hObj As Integer
        Dim textTxt As String
        Dim textPict As String
        Dim nItemCnt As Integer = 0
        Dim nWndNo As Integer

        textTxt = m_edtText1.Text
        textPict = m_edtPicture.Text

        GetSplitWnd(nWndRect) 
        hObj = CP5200_Program_Create(m_edtWidth.Text, m_edtHeight.Text, &H77)
        If hObj Then
            If CP5200_Program_SetProperty(hObj, &HFFFF, 1) > 0 Then
                nWndNo = CP5200_Program_AddPlayWindow(hObj, nWndRect(0), nWndRect(1), nWndRect(2) - nWndRect(0), nWndRect(3) - nWndRect(1))
                If nWndNo >= 0 Then
                    CP5200_Program_SetWindowProperty(hObj, nWndNo, &H30, 1)      
                    If (CP5200_Program_AddText(hObj, nWndNo, textTxt, 16, &HFF, &HFFFF, 100, 3) >= 0) Then
                        nItemCnt = nItemCnt + 1
                    End If
                End If

                nWndNo = CP5200_Program_AddPlayWindow(hObj, nWndRect(4), nWndRect(5), nWndRect(6) - nWndRect(4), nWndRect(7) - nWndRect(5))
                If (nWndNo >= 0) Then
                    If CP5200_Program_AddPicture(hObj, nWndNo, textPict, 2, &HFFFF, 100, 3, 0) >= 0 Then
                        nItemCnt = nItemCnt + 1
                    End If
                End If

                If (nItemCnt > 0 And CP5200_Program_SaveToFile(hObj, GetProgramFileName()) >= 0) Then
                    bRet = True
                End If
            End If
            CP5200_Program_Destroy(hObj)
        End If

        If bRet Then
            MessageBox.Show("Successful")
        Else
            MessageBox.Show("Fail")
        End If
    End Sub

    Private Sub MakePlaybill_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles MakePlaybill.Click
        Dim bRet As Boolean = False
        Dim hObj As Integer = CP5200_Playbill_Create(m_edtWidth.Text, m_edtHeight.Text, &H77)
        If hObj Then
            If CP5200_Playbill_AddFile(hObj, GetProgramFileName()) >= 0 Then
                If CP5200_Playbill_SaveToFile(hObj, GetPlaybillFileName()) = 0 Then
                    bRet = True
                End If
            End If
            CP5200_Playbill_Destroy(hObj)
        End If

        If bRet Then
            MessageBox.Show("Successful")
        Else
            MessageBox.Show("Fail")
        End If
    End Sub

    Private Sub Upload_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles Upload.Click
        Dim nUploadCnt As Integer = 0

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                If CP5200_RS232_UploadFile(m_nCardID, GetProgramFileName(), GetProgramFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If CP5200_RS232_UploadFile(m_nCardID, GetPlaybillFileName(), GetPlaybillFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If nUploadCnt > 0 Then
                    CP5200_RS232_RestartApp(m_nCardID)
                End If
            Else
                If CP5200_Net_UploadFile(m_nCardID, GetProgramFileName(), GetProgramFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If CP5200_Net_UploadFile(m_nCardID, GetPlaybillFileName(), GetPlaybillFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If nUploadCnt > 0 Then
                    CP5200_Net_RestartApp(m_nCardID)
                End If
            End If
        End If
        MessageBox.Show("Upload 2 files ," & CStr(nUploadCnt) & " successful ," & CStr(2 - nUploadCnt) & " failed!")
    End Sub
End Class
