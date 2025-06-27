VERSION 5.00
Begin VB.Form Form1 
   Caption         =   "CPower Demo"
   ClientHeight    =   4965
   ClientLeft      =   60
   ClientTop       =   450
   ClientWidth     =   10200
   LinkTopic       =   "Form1"
   ScaleHeight     =   4965
   ScaleWidth      =   10200
   StartUpPosition =   3  
   Begin VB.CommandButton btnSetBright 
      Caption         =   "Set Brightness"
      Height          =   375
      Left            =   4320
      TabIndex        =   36
      Top             =   4440
      Width           =   1455
   End
   Begin VB.Frame Frame2 
      Caption         =   "Make program/playbill and upload"
      Height          =   2175
      Left            =   6120
      TabIndex        =   32
      Top             =   2640
      Width           =   3855
      Begin VB.CommandButton Upload 
         Caption         =   "Upload and restart App"
         Height          =   375
         Left            =   720
         TabIndex        =   35
         Top             =   1680
         Width           =   2415
      End
      Begin VB.CommandButton MakePLaybill 
         Caption         =   "Make Playbill"
         Height          =   375
         Left            =   720
         TabIndex        =   34
         Top             =   1080
         Width           =   2415
      End
      Begin VB.CommandButton MakeProgram 
         Caption         =   "Make Program"
         Height          =   375
         Left            =   720
         TabIndex        =   33
         Top             =   435
         Width           =   2415
      End
   End
   Begin VB.TextBox m_edtSelProgram 
      Height          =   375
      Left            =   8040
      TabIndex        =   31
      Text            =   "1"
      Top             =   2040
      Width           =   1215
   End
   Begin VB.CommandButton btnPlayOneProgram 
      Caption         =   "Play One Program"
      Height          =   375
      Left            =   6120
      TabIndex        =   30
      Top             =   2040
      Width           =   1815
   End
   Begin VB.ComboBox WndNo 
      Height          =   300
      ItemData        =   "CPower_VB.frx":0000
      Left            =   8040
      List            =   "CPower_VB.frx":000A
      Style           =   2  'Dropdown List
      TabIndex        =   29
      Top             =   1515
      Width           =   1215
   End
   Begin VB.CommandButton btnSetTime 
      Caption         =   "Set Time"
      Height          =   375
      Left            =   2520
      TabIndex        =   27
      Top             =   4440
      Width           =   1455
   End
   Begin VB.TextBox m_edtStaticText 
      Height          =   375
      Left            =   2520
      TabIndex        =   26
      Text            =   "Welcome to !"
      Top             =   3840
      Width           =   3255
   End
   Begin VB.TextBox m_edtPicture 
      Height          =   375
      Left            =   2520
      TabIndex        =   25
      Text            =   "test.bmp"
      Top             =   3240
      Width           =   3255
   End
   Begin VB.TextBox m_edtText1 
      Height          =   975
      Left            =   2520
      MultiLine       =   -1  'True
      TabIndex        =   24
      Text            =   "CPower_VB.frx":0014
      Top             =   2040
      Width           =   3255
   End
   Begin VB.TextBox m_edtHeight 
      Height          =   375
      Left            =   4800
      TabIndex        =   23
      Text            =   "32"
      Top             =   1440
      Width           =   855
   End
   Begin VB.TextBox m_edtWidth 
      Height          =   375
      Left            =   3120
      TabIndex        =   22
      Text            =   "64"
      Top             =   1440
      Width           =   855
   End
   Begin VB.CommandButton btnSendClock 
      Caption         =   "Send Clock"
      Height          =   375
      Left            =   120
      TabIndex        =   19
      Top             =   4440
      Width           =   1935
   End
   Begin VB.CommandButton btnSendStaticText 
      Caption         =   "Send Static Text"
      Height          =   375
      Left            =   120
      TabIndex        =   18
      Top             =   3840
      Width           =   1935
   End
   Begin VB.CommandButton btnSendPicture 
      Caption         =   "Send Picture"
      Height          =   375
      Left            =   120
      TabIndex        =   17
      Top             =   3240
      Width           =   1935
   End
   Begin VB.CommandButton btnSendText 
      Caption         =   "Send Text"
      Height          =   375
      Left            =   120
      TabIndex        =   16
      Top             =   2040
      Width           =   1935
   End
   Begin VB.CommandButton btnSplitWnd 
      Caption         =   "Make two window"
      Height          =   375
      Left            =   120
      TabIndex        =   15
      Top             =   1440
      Width           =   1935
   End
   Begin VB.Frame Frame1 
      Height          =   1215
      Left            =   120
      TabIndex        =   0
      Top             =   120
      Width           =   9975
      Begin VB.TextBox IDCode 
         Height          =   375
         Left            =   8280
         TabIndex        =   14
         Text            =   "255.255.255.255"
         Top             =   720
         Width           =   1575
      End
      Begin VB.TextBox IPPort 
         Height          =   375
         Left            =   5160
         TabIndex        =   13
         Text            =   "5200"
         Top             =   720
         Width           =   1575
      End
      Begin VB.TextBox IPAddr 
         Height          =   375
         Left            =   2400
         TabIndex        =   12
         Text            =   "192.168.1.100"
         Top             =   720
         Width           =   1575
      End
      Begin VB.ComboBox m_cmbID 
         Height          =   300
         Left            =   8280
         Style           =   2  'Dropdown List
         TabIndex        =   8
         Top             =   240
         Width           =   1575
      End
      Begin VB.ComboBox m_cmbBaudrate 
         Height          =   300
         ItemData        =   "CPower_VB.frx":0027
         Left            =   5160
         List            =   "CPower_VB.frx":0040
         Style           =   2  'Dropdown List
         TabIndex        =   6
         Top             =   240
         Width           =   1575
      End
      Begin VB.ComboBox m_cmbPort 
         Height          =   300
         Left            =   2400
         Style           =   2  'Dropdown List
         TabIndex        =   4
         Top             =   240
         Width           =   1575
      End
      Begin VB.OptionButton RadioBtnNetWork 
         Caption         =   "Network"
         Height          =   375
         Left            =   120
         TabIndex        =   2
         Top             =   720
         Width           =   1215
      End
      Begin VB.OptionButton RadioBtnCom 
         Caption         =   "RS232/485"
         Height          =   375
         Left            =   120
         TabIndex        =   1
         Top             =   240
         Width           =   1215
      End
      Begin VB.Label Label6 
         Caption         =   "ID code"
         Height          =   255
         Left            =   6960
         TabIndex        =   11
         Top             =   840
         Width           =   855
      End
      Begin VB.Label Label5 
         Caption         =   "IP Port"
         Height          =   255
         Left            =   4200
         TabIndex        =   10
         Top             =   840
         Width           =   855
      End
      Begin VB.Label Label4 
         Caption         =   "IP Addr"
         Height          =   255
         Left            =   1440
         TabIndex        =   9
         Top             =   840
         Width           =   855
      End
      Begin VB.Label Label3 
         Caption         =   "Controller ID"
         Height          =   375
         Left            =   6960
         TabIndex        =   7
         Top             =   240
         Width           =   1215
      End
      Begin VB.Label Label2 
         Caption         =   "Baudrate"
         Height          =   375
         Left            =   4200
         TabIndex        =   5
         Top             =   240
         Width           =   855
      End
      Begin VB.Label Label1 
         Caption         =   "COM Port"
         Height          =   375
         Left            =   1440
         TabIndex        =   3
         Top             =   240
         Width           =   855
      End
   End
   Begin VB.Label Label9 
      Caption         =   "Select send window"
      Height          =   375
      Left            =   6120
      TabIndex        =   28
      Top             =   1560
      Width           =   1695
   End
   Begin VB.Label Label8 
      Caption         =   "Height"
      Height          =   255
      Left            =   3960
      TabIndex        =   21
      Top             =   1560
      Width           =   735
   End
   Begin VB.Label Label7 
      Caption         =   "Width"
      Height          =   255
      Left            =   2520
      TabIndex        =   20
      Top             =   1560
      Width           =   615
   End
End
Attribute VB_Name = "Form1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False

'Begin
    Private Declare Function CP5200_Playbill_Create Lib "CP5200.dll" (ByVal width As Long, ByVal height As Long, ByVal color As Byte) As Long
    Private Declare Function CP5200_Playbill_Destroy Lib "CP5200.dll" (ByVal hObj As Long) As Long
    Private Declare Function CP5200_Playbill_AddFile Lib "CP5200.dll" (ByVal hObj As Long, ByVal pText As String) As Long
    Private Declare Function CP5200_Playbill_SaveToFile Lib "CP5200.dll" (ByVal hObj As Long, ByVal pText As String) As Long

    Private Declare Function CP5200_Program_Create Lib "CP5200.dll" (ByVal width As Long, ByVal height As Long, ByVal color As Byte) As Long
    Private Declare Function CP5200_Program_Destroy Lib "CP5200.dll" (ByVal hObj As Long) As Long
    Private Declare Function CP5200_Program_SetProperty Lib "CP5200.dll" (ByVal hObj As Long, ByVal nPropertyValue As Long, ByVal nPropertyID As Long) As Long
    Private Declare Function CP5200_Program_AddPlayWindow Lib "CP5200.dll" (ByVal hObj As Long, ByVal x As Long, ByVal Y As Long, ByVal cx As Long, ByVal cy As Long) As Long
    Private Declare Function CP5200_Program_SetWindowProperty Lib "CP5200.dll" (ByVal hObj As Long, ByVal nWndNo As Long, ByVal nPropertyValue As Long, ByVal nPropertyID As Long) As Long
    Private Declare Function CP5200_Program_AddText Lib "CP5200.dll" (ByVal hObj As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal nFontSize As Long, ByVal crColor As Long, ByVal nEffect As Long, ByVal nSpeed As Long, ByVal nStay As Long) As Long
    Private Declare Function CP5200_Program_AddPicture Lib "CP5200.dll" (ByVal hObj As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal nMode As Long, ByVal nEffect As Long, ByVal nSpeed As Long, ByVal nStay As Long, ByVal nCompress As Long) As Long
    Private Declare Function CP5200_Program_SaveToFile Lib "CP5200.dll" (ByVal hObj As Long, ByVal pText As String) As Long


    'MakeData
    Private Declare Function CP5200_CommData_Create Lib "CP5200.dll" (ByVal nCommType As Long, ByVal byCardID As Byte, ByVal dwIDCode As Long) As Long
    Private Declare Function CP5200_CommData_Destroy Lib "CP5200.dll" (ByVal hObj As Long) As Long
    Private Declare Function CP5200_MakeWriteBrightnessData Lib "CP5200.dll" (ByVal hObj As Long, ByRef pBuf As Byte, ByVal nBufSize As Long, ByRef pBrightnessBuffer As Byte) As Long
    Private Declare Function CP5200_ParseWriteBrightnessRet Lib "CP5200.dll" (ByVal hObj As Long, ByRef pBuf As Byte, ByVal nBufSize As Long) As Long
    
    'Rs232/485
    Private Declare Function CP5200_RS232_InitEx Lib "CP5200.dll" (ByVal fName As String, ByVal nBaudrate As Long, ByVal nTimeout As Long) As Long
    Private Declare Function CP5200_RS232_Open Lib "CP5200.dll" () As Long
    Private Declare Function CP5200_RS232_Close Lib "CP5200.dll" () As Long
    Private Declare Function CP5200_RS232_Write Lib "CP5200.dll" (ByRef pBuf As Byte, ByVal nLength As Long) As Long
    Private Declare Function CP5200_RS232_ReadEx Lib "CP5200.dll" (ByRef pBuf As Byte, ByVal nBufSize As Long) As Long
    
    Private Declare Function CP5200_RS232_PlaySelectedPrg Lib "CP5200.dll" (ByVal nCardID As Long, ByRef pSelected As Long, ByVal nSelCnt As Long, ByVal nOption As Long) As Long
    Private Declare Function CP5200_RS232_SendText Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal crColor As Long, ByVal nFontSize As Long, ByVal nSpeed As Long, ByVal nEffect As Long, ByVal nStayTime As Long, ByVal nAlignment As Long) As Long
    Private Declare Function CP5200_RS232_SendPicture Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal nPosX As Long, ByVal nPosY As Long, ByVal nCx As Long, ByVal nCy As Long, ByVal pPictureFile As String, ByVal nSpeed As Long, ByVal nEffect As Long, ByVal nStayTime As Long, ByVal nPictRef As Long) As Long
    Private Declare Function CP5200_RS232_SendStatic Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal crColor As Long, ByVal nFontSize As Long, ByVal nAlignment As Long, ByVal x As Long, ByVal Y As Long, ByVal cx As Long, ByVal cy As Long) As Long
    Private Declare Function CP5200_RS232_SendClock Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWinNo As Long, ByVal nStayTime As Long, ByVal nCalendar As Long, ByVal nFormat As Long, ByVal nContent As Long, ByVal nFont As Long, ByVal nRed As Long, ByVal nGreen As Long, ByVal nBlue As Long, ByVal pTxt As String) As Long
    Private Declare Function CP5200_RS232_SetTime Lib "CP5200.dll" (ByVal nCardID As Long, ByRef pInfo As Byte) As Long
    Private Declare Function CP5200_RS232_SplitScreen Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nScrWidth As Long, ByVal ScrHeight As Long, ByVal nWndCnt As Long, ByRef pWndRects As Long) As Long
    Private Declare Function CP5200_RS232_UploadFile Lib "CP5200.dll" (ByVal nCardID As Long, ByVal pSourceFilename As String, ByVal pTargetFilename As String) As Long
    Private Declare Function CP5200_RS232_RestartApp Lib "CP5200.dll" (ByVal nCardID As Long) As Long

    
    'NetWork
    Private Declare Function CP5200_Net_Init Lib "CP5200.dll" (ByVal dwIP As Long, ByVal nIPPort As Long, ByVal dwIDCode As Long, ByVal nTimeout As Long) As Long
    Private Declare Function CP5200_Net_Connect Lib "CP5200.dll" () As Long
    Private Declare Function CP5200_Net_Disconnect Lib "CP5200.dll" () As Long
    Private Declare Function CP5200_Net_Write Lib "CP5200.dll" (ByRef pBuf As Byte, ByVal nLength As Long) As Long
    Private Declare Function CP5200_Net_Read Lib "CP5200.dll" (ByRef pBuf As Byte, ByVal nBufSize As Long) As Long
    
    Private Declare Function CP5200_Net_PlaySelectedPrg Lib "CP5200.dll" (ByVal nCardID As Long, ByRef pSelected As Long, ByVal nSelCnt As Long, ByVal nOption As Long) As Long
    Private Declare Function CP5200_Net_SendText Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal crColor As Long, ByVal nFontSize As Long, ByVal nSpeed As Long, ByVal nEffect As Long, ByVal nStayTime As Long, ByVal nAlignment As Long) As Long
    Private Declare Function CP5200_Net_SendPicture Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal nPosX As Long, ByVal nPosY As Long, ByVal nCx As Long, ByVal nCy As Long, ByVal pPictureFile As String, ByVal nSpeed As Long, ByVal nEffect As Long, ByVal nStayTime As Long, ByVal nPictRef As Long) As Long
    Private Declare Function CP5200_Net_SendStatic Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWndNo As Long, ByVal pText As String, ByVal crColor As Long, ByVal nFontSize As Long, ByVal nAlignment As Long, ByVal x As Long, ByVal Y As Long, ByVal cx As Long, ByVal cy As Long) As Long
    Private Declare Function CP5200_Net_SendClock Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nWinNo As Long, ByVal nStayTime As Long, ByVal nCalendar As Long, ByVal nFormat As Long, ByVal nContent As Long, ByVal nFont As Long, ByVal nRed As Long, ByVal nGreen As Long, ByVal nBlue As Long, ByVal pTxt As String) As Long
    Private Declare Function CP5200_Net_SetTime Lib "CP5200.dll" (ByVal nCardID As Long, ByRef pInfo As Byte) As Long
    Private Declare Function CP5200_Net_SplitScreen Lib "CP5200.dll" (ByVal nCardID As Long, ByVal nScrWidth As Long, ByVal ScrHeight As Long, ByVal nWndCnt As Long, ByRef pWndRects As Long) As Long
    Private Declare Function CP5200_Net_UploadFile Lib "CP5200.dll" (ByVal nCardID As Long, ByVal pSourceFilename As String, ByVal pTargetFilename As String) As Long
    Private Declare Function CP5200_Net_RestartApp Lib "CP5200.dll" (ByVal nCardID As Long) As Long

    'End
    
    
    
    Private Type SYSTEMTIME
          wYear As Integer
          wMonth As Integer
          wDayOfWeek As Integer
          wDay As Integer
          wHour As Integer
          wMinute As Integer
          wSecond As Integer
          wMilliseconds As Integer
    End Type
    
    Private Declare Sub GetLocalTime Lib "kernel32" (lpSystemTime As SYSTEMTIME)
    
     
    
    
    
    Dim m_nTimeout As Long   
    Dim m_nCommType As Byte
    Dim m_baudtbl(0 To 6) As Long
    
Private Function CountIF(ByRef lzExpr As String, ByRef nChar As String) As Integer
        Dim x, iCount As Integer
        Dim sByte() As Byte
        sByte() = StrConv(lzExpr, vbformunicode)
                
        For x = LBound(sByte) To UBound(sByte) Step 2
            If sByte(x) = Asc(nChar) Then iCount = iCount + 1
        Next
        x = 0
        Erase sByte
        
        CountIF = iCount
    End Function
    
Private Function MAKEIPADDRESS(ByVal b1 As Long, ByVal b2 As Long, ByVal b3 As Long, ByVal b4 As Long) As Long
        MAKEIPADDRESS = ((b1 And &H7F) * &H1000000 Or (b1 And &H80) <> 0 And &H80000000) Or (b2 * &H10000) Or (b3 * &H100) Or (b4)
End Function

    Private Function GetIP(ByVal Value As String) As Long
        If CountIF(Value, ".") < 3 Then
            MessageBox.Show ("IP address format error!")
            GetIP = 0
            Return
        Else
            Dim mByte(3) As Byte
            Dim mInt(3) As Integer
            Dim i As Integer
            Dim vIp() As String

            vIp = Split(Value, ".") 
            For i = 0 To 3
                mInt(i) = vIp(3 - i)
                If mInt(i) > 255 Or mInt(i) < 0 Then
                    Erase vIp
                    MessageBox.Show ("IP address format error!")
                    GetIP = 0
                    Return
                Else
                    mByte(i) = mInt(i)
                End If
            Next i
            Erase vIp
            GetIP = MAKEIPADDRESS(mByte(3), mByte(2), mByte(1), mByte(0))
        End If
    End Function
    

    
Private Function InitComm() As Long
        Dim nRet As Long
        Dim dwIPAddr As Long
        Dim dwIDCode As Long

        nRet = 0
        If m_nCommType = 0 Then
            Dim strPort As String
            m_nPort = m_cmbPort.ListIndex + 1
            strPort = "COM" + CStr(m_nPort)
            Call CP5200_RS232_InitEx(strPort, m_baudtbl(m_cmbBaudrate.ListIndex), m_nTimeout)
            nRet = 1
        Else
            dwIPAddr = GetIP(IPAddr.text)
            If dwIPAddr <> 0 Then
                dwIDCode = GetIP(IDCode.text)
                If dwIDCode <> 0 Then
                    Call CP5200_Net_Init(dwIPAddr, IPPort.text, dwIDCode, m_nTimeout)
                    nRet = 1
                End If
            End If
        End If
        InitComm = nRet
End Function

Private Sub GetSplitWnd(ByRef rcWins() As Long)
        rcWins(0) = 0
        rcWins(1) = 0
        rcWins(2) = m_edtWidth.text / 2
        rcWins(3) = m_edtHeight.text
        rcWins(4) = m_edtWidth.text / 2
        rcWins(5) = 0
        rcWins(6) = m_edtWidth.text
        rcWins(7) = m_edtHeight.text
End Sub

Private Sub EnableCtrl()
        m_cmbPort.Enabled = (m_nCommType = 0)
        m_cmbBaudrate.Enabled = (m_nCommType = 0)
        IPAddr.Enabled = (m_nCommType = 1)
        IPPort.Enabled = (m_nCommType = 1)
        IDCode.Enabled = (m_nCommType = 1)
End Sub
   

Private Sub btnPlayOneProgram_Click()
        Dim ret As Integer
        Dim prg As Long
        Dim strPrg(2) As Long

        prg = m_edtSelProgram.text
        If prg < 0 Then
            prg = 0
        End If
        strPrg(0) = prg
        strPrg(1) = 0

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_PlaySelectedPrg(m_cmbID.ListIndex + 1, strPrg(0), 1, 0)
            Else
                ret = CP5200_Net_PlaySelectedPrg(m_cmbID.ListIndex + 1, strPrg(0), 1, 0)
            End If

            If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub

Private Sub btnSendClock_Click()
        Dim ret As Integer
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendClock(m_cmbID.ListIndex + 1, WndNo.ListIndex, 3, 0, 7, 7, 1, 255, 255, 255, "Date")
            Else
                ret = CP5200_Net_SendClock(m_cmbID.ListIndex + 1, WndNo.ListIndex, 3, 0, 7, 7, 1, 255, 255, 255, "Date")
            End If

            If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub

Private Sub btnSendPicture_Click()
        Dim ret As Integer
        Dim text As String
        Dim nWndRect(0 To 7) As Long
        Call GetSplitWnd(nWndRect)
        text = m_edtPicture.text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendPicture(m_cmbID.ListIndex + 1, WndNo.ListIndex, 0, 0, nWndRect(2 + WndNo.ListIndex * 4) - nWndRect(0 + WndNo.ListIndex * 4), nWndRect(3 + WndNo.ListIndex * 4) - nWndRect(1 + WndNo.ListIndex * 4), text, 1, 0, 3, 0)
            Else
                ret = CP5200_Net_SendPicture(m_cmbID.ListIndex + 1, WndNo.ListIndex, 0, 0, nWndRect(2 + WndNo.ListIndex * 4) - nWndRect(0 + WndNo.ListIndex * 4), nWndRect(3 + WndNo.ListIndex * 4) - nWndRect(1 + WndNo.ListIndex * 4), text, 1, 0, 3, 0)
            End If

             If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub

Private Sub btnSendStaticText_Click()
        Dim ret As Integer
        Dim text As String
        Dim nWndRect(0 To 7) As Long
        Call GetSplitWnd(nWndRect)
        text = m_edtStaticText.text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendStatic(m_cmbID.ListIndex + 1, WndNo.ListIndex, text, RGB(255, 0, 0), 16, 0, 0, 0, nWndRect(2 + WndNo.ListIndex * 4) - nWndRect(0 + WndNo.ListIndex * 4), nWndRect(3 + WndNo.ListIndex * 4) - nWndRect(1 + WndNo.ListIndex * 4))
            Else
                ret = CP5200_Net_SendStatic(m_cmbID.ListIndex + 1, WndNo.ListIndex, text, RGB(255, 0, 0), 16, 0, 0, 0, nWndRect(2 + WndNo.ListIndex * 4) - nWndRect(0 + WndNo.ListIndex * 4), nWndRect(3 + WndNo.ListIndex * 4) - nWndRect(1 + WndNo.ListIndex * 4))
            End If


             If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub

Private Sub btnSendText_Click()
        Dim ret As Integer
        Dim text As String
        text = m_edtText1.text
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SendText(m_cmbID.ListIndex + 1, WndNo.ListIndex, text, RGB(255, 0, 0), 16, 3, 0, 3, 5)
            Else
                ret = CP5200_Net_SendText(m_cmbID.ListIndex + 1, WndNo.ListIndex, text, RGB(255, 0, 0), 16, 3, 0, 3, 5)
            End If


            If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If

End Sub



Private Sub btnSetTime_Click()
        Dim ret As Integer
        Dim byTime(0 To 6) As Byte
        Dim st As SYSTEMTIME
        GetLocalTime st
        byTime(0) = st.wSecond
        byTime(1) = st.wMinute
        byTime(2) = st.wHour
        byTime(3) = st.wDayOfWeek
        byTime(4) = st.wDay
        byTime(5) = st.wMonth
        byTime(6) = st.wYear - 2000

        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SetTime(m_cmbID.ListIndex + 1, byTime(0))
            Else
                ret = CP5200_Net_SetTime(m_cmbID.ListIndex + 1, byTime(0))
            End If

             If ret = 1 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub

Private Sub btnSplitWnd_Click()
        Dim ret As Long
        Dim nWndRect(0 To 7) As Long
        Call GetSplitWnd(nWndRect)

        If InitComm = 1 Then
            If m_nCommType = 0 Then
                ret = CP5200_RS232_SplitScreen(m_cmbID.ListIndex + 1, m_edtWidth.text, m_edtHeight.text, 2, nWndRect(0))
            Else
                ret = CP5200_Net_SplitScreen(m_cmbID.ListIndex + 1, m_edtWidth.text, m_edtHeight.text, 2, nWndRect(0))
            End If
            
            If ret >= 0 Then
                MsgBox ("Successful")
            Else
                MsgBox ("Fail")
            End If
        End If
End Sub


Private Sub Form_Load()
        Dim strTemp As String
        Dim i As Long
        For i = 1 To 100
            strTemp = CStr(i)
            m_cmbID.AddItem (strTemp)
            strTemp = "COM" + strTemp
            m_cmbPort.AddItem (strTemp)
        Next i
        
        m_cmbID.ListIndex = 0
        m_cmbPort.ListIndex = 0
        m_cmbBaudrate.ListIndex = 0
        WndNo.ListIndex = 0
        
       
        m_nTimeout = 600
        m_nCommType = 0
               
        m_baudtbl(0) = 115200
        m_baudtbl(1) = 57600
        m_baudtbl(2) = 38400
        m_baudtbl(3) = 19200
        m_baudtbl(4) = 9600
        m_baudtbl(5) = 4800
        m_baudtbl(6) = 2400
End Sub



Private Sub RadioBtnCom_Click()
        m_nCommType = 0
        Call EnableCtrl
End Sub

Private Sub RadioBtnNetWork_Click()
        m_nCommType = 1
        Call EnableCtrl
End Sub

   Private Function GetProgramFileName() As String
        Dim strName As String
        strName = Format(m_cmbID.ListIndex + 1, "0000") & "0000.lpb"
        GetProgramFileName = strName
    End Function

    Private Function GetPlaybillFileName() As String
        GetPlaybillFileName = "playbill.lpp"
    End Function
    
Private Sub MakeProgram_Click()
        Dim bRet As Boolean
        Dim hObj As Long
        Dim textTxt As String
        Dim textPict As String
        Dim nItemCnt As Integer
        Dim nWndNo As Integer
        Dim nWndRect(0 To 7) As Long
              
        bRet = False
        nItemCnt = 0
        textTxt = m_edtText1.text
        textPict = m_edtPicture.text

        Call GetSplitWnd(nWndRect)  
        hObj = CP5200_Program_Create(m_edtWidth.text, m_edtHeight.text, &H77)
        If hObj Then
            If CP5200_Program_SetProperty(hObj, 65535, 1) > 0 Then
                nWndNo = CP5200_Program_AddPlayWindow(hObj, nWndRect(0), nWndRect(1), nWndRect(2) - nWndRect(0), nWndRect(3) - nWndRect(1))
                If nWndNo >= 0 Then
                    Call CP5200_Program_SetWindowProperty(hObj, nWndNo, &H30, 1)      'ÉèÖÃ´°¿Ú±ß¿ò
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
            CP5200_Program_Destroy (hObj)
        End If
        
        If bRet Then
            MsgBox ("Successful")
        Else
            MsgBox ("Fail")
        End If

End Sub

Private Sub MakePLaybill_Click()
        Dim bRet As Boolean
        Dim hObj As Long
        bRet = False
        hObj = CP5200_Playbill_Create(m_edtWidth.text, m_edtHeight.text, &H77)
        If hObj Then
            If CP5200_Playbill_AddFile(hObj, GetProgramFileName()) >= 0 Then
                If CP5200_Playbill_SaveToFile(hObj, GetPlaybillFileName()) = 0 Then
                    bRet = True
                End If
            End If
            CP5200_Playbill_Destroy (hObj)
        End If
        
        If bRet Then
            MsgBox ("Successful")
        Else
            MsgBox ("Fail")
        End If
End Sub

Private Sub Upload_Click()
        Dim nUploadCnt As Integer
        
        nUploadCnt = 0
        If InitComm() = 1 Then
            If m_nCommType = 0 Then
                If CP5200_RS232_UploadFile(m_cmbID.ListIndex + 1, GetProgramFileName(), GetProgramFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If CP5200_RS232_UploadFile(m_cmbID.ListIndex + 1, GetPlaybillFileName(), GetPlaybillFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If nUploadCnt > 0 Then
                    CP5200_RS232_RestartApp (m_cmbID.ListIndex + 1)
                End If
            Else
                If CP5200_Net_UploadFile(m_cmbID.ListIndex + 1, GetProgramFileName(), GetProgramFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If CP5200_Net_UploadFile(m_cmbID.ListIndex + 1, GetPlaybillFileName(), GetPlaybillFileName()) = 0 Then
                    nUploadCnt = nUploadCnt + 1
                End If

                If nUploadCnt > 0 Then
                    CP5200_Net_RestartApp (m_cmbID.ListIndex + 1)
                End If
            End If
        End If
        MsgBox ("Upload 2 files ," & CStr(nUploadCnt) & " successful ," & CStr(2 - nUploadCnt) & " failed!")

End Sub

Private Sub btnSetBright_Click()
  Dim byBuf(0 To 99) As Byte
  Dim byRet(0 To 99) As Byte
  Dim byRight(0 To 23) As Byte
  Dim hObj, lDataLen, lReadLen, lRet, lSucc As Long
  lDataLen = 0
  lReadLen = 0
  lRet = 0
  lSucc = 0

  For i = 0 To 99
    byBuf(i) = 0
    byRet(i) = 0
    If i <= 23 Then
      byRight(i) = 30
    End If
  Next i
  
  hObj = CP5200_CommData_Create(m_nCommType, m_cmbID.ListIndex + 1, GetIP(IDCode.text))
  If hObj Then
    lDataLen = CP5200_MakeWriteBrightnessData(hObj, byBuf(0), 100, byRight(0))
    If lDataLen > 0 Then
      If InitComm() = 1 Then
        If m_nCommType = 0 Then
          lRet = CP5200_RS232_Open()
          If lRet = 1 Then
            lRet = CP5200_RS232_Write(byBuf(0), lDataLen)
            If lRet = 1 Then
              lReadLen = CP5200_RS232_ReadEx(byRet(0), 100)
            End If
            lRet = CP5200_RS232_Close()
          End If
        Else
          lRet = CP5200_Net_Connect()
          If lRet = 1 Then
            lRet = CP5200_Net_Write(byBuf(0), lDataLen)
            If lRet = 1 Then
              lReadLen = CP5200_Net_Read(byRet(0), 100)
            End If
            lRet = CP5200_Net_Disconnect()
          End If
        End If
      End If
    End If
    
    If lReadLen > 0 Then
      lSucc = CP5200_ParseWriteBrightnessRet(hObj, byRet(0), lReadLen)
    End If
    lRet = CP5200_CommData_Destroy(hObj)
  End If
  
  If lSucc = 1 Then
    MsgBox ("Successful")
  Else
    MsgBox ("Fail")
  End If
  
End Sub


