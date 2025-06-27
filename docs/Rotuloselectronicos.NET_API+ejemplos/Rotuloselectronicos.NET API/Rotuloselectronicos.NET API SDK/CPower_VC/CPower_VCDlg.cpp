// CPower_VCDlg.cpp : implementation file
//

#include "stdafx.h"
#include "CPower_VC.h"
#include "CPower_VCDlg.h"
#include ".\cpower_vcdlg.h"

#include "CP5200API.h"
#pragma comment (lib, "cp5200.lib")

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

const long glBaudrete[] = { 115200 , 57600 , 38400 , 19200 , 9600 , 4800 , 2400 };
#define _countof(array) (sizeof(array)/sizeof(array[0]))


class CAboutDlg : public CDialog
{
public:
	CAboutDlg();
	
	// Dialog Data
	//{{AFX_DATA(CAboutDlg)
	enum { IDD = IDD_ABOUTBOX };
	//}}AFX_DATA
	
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CAboutDlg)
protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	//}}AFX_VIRTUAL
	
	// Implementation
protected:
	//{{AFX_MSG(CAboutDlg)
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
	//{{AFX_DATA_INIT(CAboutDlg)
	//}}AFX_DATA_INIT
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CAboutDlg)
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
//{{AFX_MSG_MAP(CAboutDlg)
// No message handlers
//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CPower_VCDlg dialog

CPower_VCDlg::CPower_VCDlg(CWnd* pParent /*=NULL*/)
: CDialog(CPower_VCDlg::IDD, pParent)
, m_nCommType(0)
, m_nPort(5200)
, m_nWidth(64)
, m_nHeight(32)
, m_nProNo(1)
{
	//{{AFX_DATA_INIT(CPower_VCDlg)
	// NOTE: the ClassWizard will add member initialization here
	//}}AFX_DATA_INIT
	// Note that LoadIcon does not require a subsequent DestroyIcon in Win32
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
	m_nTimeOut = 600;
}

void CPower_VCDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_PORT, m_cmbPort);
	DDX_Control(pDX, IDC_BAUDRATE, m_cmbBaudrate);
	DDX_Control(pDX, IDC_ID, m_cmbCardID);
	DDX_Control(pDX, IDC_IPADDR, m_ctrlIPAddr);
	DDX_Control(pDX, IDC_IDCODE, m_ctrlIDCode);
	DDX_Text(pDX, IDC_PORT2, m_nPort);
	DDX_Text(pDX, IDC_EDIT1, m_nWidth);
	DDX_Text(pDX, IDC_EDIT2, m_nHeight);
	DDX_Control(pDX, IDC_ID2, m_cmbWndNo);
	DDX_Text(pDX, IDC_EDIT_PRONO, m_nProNo);
}

BEGIN_MESSAGE_MAP(CPower_VCDlg, CDialog)
//{{AFX_MSG_MAP(CPower_VCDlg)
ON_WM_SYSCOMMAND()
ON_WM_PAINT()
ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BTN_MAKE_PROGRAM, OnBtnMakeProgram)
	ON_BN_CLICKED(IDC_BTN_MAKE_PLAYBILL, OnBtnMakePlaybill)
	ON_BN_CLICKED(IDC_BTN_UPLOAD, OnBtnUpload)
	//}}AFX_MSG_MAP
ON_BN_CLICKED(IDC_RADIO1, OnBnClickedRadio1)
ON_BN_CLICKED(IDC_RADIO2, OnBnClickedRadio2)
ON_BN_CLICKED(IDC_BTN_SPLIT_WND, OnBnClickedBtnSplitWnd)
ON_BN_CLICKED(IDC_BTN_SEND_TEXT, OnBnClickedBtnSendText)
ON_BN_CLICKED(IDC_BTN_SEND_PICT, OnBnClickedBtnSendPict)
ON_BN_CLICKED(IDC_BTN_SEND_STATIC_TEXT, OnBnClickedBtnSendStaticText)
ON_BN_CLICKED(IDC_SEND_CLOCK, OnBnClickedSendClock)
ON_BN_CLICKED(IDC_BTN_SET_TIME, OnBnClickedBtnSetTime)
ON_BN_CLICKED(IDC_BTN_PLAY_PROGRAM, OnBnClickedBtnPlayProgram)
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CPower_VCDlg message handlers

BOOL CPower_VCDlg::OnInitDialog()
{
	CDialog::OnInitDialog();
	
	// Add "About..." menu item to system menu.
	
	// IDM_ABOUTBOX must be in the system command range.
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);
	
	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}
	
	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon
	for ( int i = 1 ; i < 255 ; i++ )
	{
		CString str;
		str.Format("%d" , i );
		m_cmbCardID.AddString(str);
		m_cmbPort.AddString("COM" + str );
	}
	
	for ( int j = 0 ; j < _countof( glBaudrete ) ; j++ )		
	{
		CString str;
		str.Format("%ld" , glBaudrete[j]);
		m_cmbBaudrate.AddString(str);
	}
	
	
	m_cmbCardID.SetCurSel(0);
	m_cmbPort.SetCurSel(0);
	m_cmbBaudrate.SetCurSel(0);
	
	m_cmbWndNo.AddString("0");
	m_cmbWndNo.AddString("1");
	m_cmbWndNo.SetCurSel(0);
	
	m_ctrlIPAddr.SetAddress(0xc0a80164);
	m_ctrlIDCode.SetAddress(0xFFFFFFFF);
	((CButton*)GetDlgItem(IDC_RADIO1))->SetCheck( BST_CHECKED );
	EnableCtrl();
	
	SetDlgItemText( IDC_EDIT_TEXT , "Welcome");
	SetDlgItemText( IDC_EDIT_STATIC_TEXT , "Welcome to");
	SetDlgItemText( IDC_EDIT_PICT , "test.bmp");
	
	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CPower_VCDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CPower_VCDlg::OnPaint() 
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting
		
		SendMessage(WM_ICONERASEBKGND, (WPARAM) dc.GetSafeHdc(), 0);
		
		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;
		
		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CPower_VCDlg::OnQueryDragIcon()
{
	return (HCURSOR) m_hIcon;
}

void CPower_VCDlg::OnOK() 
{	
	//CDialog::OnOK();
}

void CPower_VCDlg::OnBnClickedRadio1()
{
	m_nCommType = 0 ;
	EnableCtrl();
}

void CPower_VCDlg::OnBnClickedRadio2()
{
	m_nCommType = 1 ;
	EnableCtrl();
}

//=====================================

void CPower_VCDlg::EnableCtrl()
{
	m_cmbPort.EnableWindow( m_nCommType == 0);
	m_cmbBaudrate.EnableWindow( m_nCommType == 0);
	//m_cmbCardID.EnableWindow( m_nCommType == 0);
	GetDlgItem(IDC_IPADDR)->EnableWindow( m_nCommType == 1);
	GetDlgItem(IDC_IDCODE)->EnableWindow( m_nCommType == 1);
	GetDlgItem(IDC_PORT2)->EnableWindow( m_nCommType == 1);
}


void CPower_VCDlg::InitComm()
{
	UpdateData();
	
	if ( m_nCommType == 1) //
	{
		DWORD dwIPAddr , dwIDCode ;
		m_ctrlIPAddr.GetAddress( dwIPAddr );
		m_ctrlIDCode.GetAddress( dwIDCode );
		CP5200_Net_Init( dwIPAddr, m_nPort, dwIDCode, m_nTimeOut );
	}
	else //
	{
		CString strPort;
		strPort.Format("%d" , m_cmbPort.GetCurSel()+1);
		CP5200_RS232_InitEx( "COM" + strPort, glBaudrete[m_cmbBaudrate.GetCurSel()], m_nTimeOut);
	}
}

void CPower_VCDlg::GetSplitWnd( RECT* rcWins )
{
	rcWins[0].left   = 0;
	rcWins[0].top    = 0;
	rcWins[0].right  = m_nWidth/2;
	rcWins[0].bottom = m_nHeight;
	
	rcWins[1].left   = m_nWidth/2;
	rcWins[1].top    = 0;
	rcWins[1].right  = m_nWidth;
	rcWins[1].bottom = m_nHeight;
}

//=====================================
void CPower_VCDlg::OnBnClickedBtnSplitWnd()
{
	UpdateData();
	//
	RECT rcWins[2];	
	GetSplitWnd( rcWins );
	
	InitComm();
    int nRet;
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SplitScreen( m_cmbCardID.GetCurSel()+1, m_nWidth, m_nHeight, 2, (const int*)rcWins);
	}
	else //
	{
		nRet = CP5200_RS232_SplitScreen(m_cmbCardID.GetCurSel()+1, m_nWidth, m_nHeight, 2, (const int*)rcWins);
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");	
}

void CPower_VCDlg::OnBnClickedBtnSendText()
{
	UpdateData();
	InitComm();
	int nRet;
	
	CString strText;
	GetDlgItemText( IDC_EDIT_TEXT , strText );
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SendText(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), strText, RGB(255, 0, 0), 16, 3, 0, 3, 5);
	}
	else //
	{
		nRet = CP5200_RS232_SendText(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), strText, RGB(255, 0, 0), 16, 3, 0, 3, 5);
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");	
}

void CPower_VCDlg::OnBnClickedBtnSendPict()
{
	UpdateData();
	InitComm();
	int nRet;
	RECT rcWins[2];	
	GetSplitWnd( rcWins );
	CString strText;
	GetDlgItemText( IDC_EDIT_PICT , strText );
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SendPicture(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(),0, 0, 
			rcWins[m_cmbWndNo.GetCurSel()].right - rcWins[m_cmbWndNo.GetCurSel()].left, 
			rcWins[m_cmbWndNo.GetCurSel()].bottom - rcWins[m_cmbWndNo.GetCurSel()].top, 
			strText, 1, 0, 3, 0);
	}
	else //
	{
		nRet = CP5200_RS232_SendPicture(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(),0, 0, 
			rcWins[m_cmbWndNo.GetCurSel()].right - rcWins[m_cmbWndNo.GetCurSel()].left, 
			rcWins[m_cmbWndNo.GetCurSel()].bottom - rcWins[m_cmbWndNo.GetCurSel()].top, 
			strText, 1, 0, 3, 0);
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

void CPower_VCDlg::OnBnClickedBtnSendStaticText()
{
	UpdateData();
	InitComm();
	int nRet;
	
	RECT rcWins[2];	
	GetSplitWnd( rcWins );
	
	CString strText;
	GetDlgItemText( IDC_EDIT_STATIC_TEXT , strText );
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SendStatic(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), strText, RGB(255, 0, 0), 16, 0, 
			0, 0, rcWins[m_cmbWndNo.GetCurSel()].right - rcWins[m_cmbWndNo.GetCurSel()].left, rcWins[m_cmbWndNo.GetCurSel()].bottom - rcWins[m_cmbWndNo.GetCurSel()].top);
	}
	else //
	{
		nRet = CP5200_RS232_SendStatic(m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), strText, RGB(255, 0, 0), 16, 0, 
			0, 0, rcWins[m_cmbWndNo.GetCurSel()].right - rcWins[m_cmbWndNo.GetCurSel()].left, rcWins[m_cmbWndNo.GetCurSel()].bottom - rcWins[m_cmbWndNo.GetCurSel()].top);
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

void CPower_VCDlg::OnBnClickedSendClock()
{
	UpdateData();
	InitComm();
	int nRet;
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SendClock( m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), 3, 0, 7, 7, 1, 255, 255, 255, "Date");
	}
	else //
	{
		nRet = CP5200_RS232_SendClock( m_cmbCardID.GetCurSel()+1, m_cmbWndNo.GetCurSel(), 3, 0, 7, 7, 1, 255, 255, 255, "Date");
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

void CPower_VCDlg::OnBnClickedBtnSetTime()
{
	UpdateData();
	InitComm();
	int nRet;
	byte byTimeInfo[7];
	COleDateTime time = COleDateTime::GetCurrentTime();
	byTimeInfo[0] = time.GetSecond();
	byTimeInfo[1] = time.GetMinute();
    byTimeInfo[2] = time.GetHour();
	byTimeInfo[3] = time.GetDayOfWeek();
	byTimeInfo[4] = time.GetDay();
	byTimeInfo[5] = time.GetMonth();
	byTimeInfo[6] = time.GetYear() - 2000 ;
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_SetTime(m_cmbCardID.GetCurSel()+1, byTimeInfo) ; 
	}
	else //
	{
		nRet = CP5200_RS232_SetTime(m_cmbCardID.GetCurSel()+1, byTimeInfo) ; 
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

void CPower_VCDlg::OnBnClickedBtnPlayProgram()
{
	UpdateData();
	InitComm();
	int nRet;
	WORD wdProNo[1];
	wdProNo[0] = m_nProNo;
	
	if ( m_nCommType == 1) //
	{
		nRet = CP5200_Net_PlaySelectedPrg(m_cmbCardID.GetCurSel()+1, wdProNo, 1, 0);
	}
	else //
	{
		nRet = CP5200_RS232_PlaySelectedPrg(m_cmbCardID.GetCurSel()+1, wdProNo, 1, 0);
	}
	
	if ( nRet >= 0)
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

//////////////////////////////////////////////////////////////////////////
//
CString CPower_VCDlg::GetProgramFileName()
{
	CString strName;
	strName.Format("%04d0000.lpb" , m_cmbCardID.GetCurSel()+1);
	return strName;
}

CString CPower_VCDlg::GetPlaybillFileName()
{
	return _T("playbill.lpp");
}
void CPower_VCDlg::OnBtnMakeProgram() 
{
	UpdateData();

	BOOL bRet = FALSE;
	HOBJECT hObj = CP5200_Program_Create( m_nWidth, m_nHeight, 0x77 );
	if ( hObj )
	{
		//
		RECT rcWins[2];	
	    GetSplitWnd( rcWins );
		if ( CP5200_Program_SetProperty( hObj , 0xFFFF , 1 ) > 0 )
		{
			int nItemCnt = 0;
			//
			int nWndNo = CP5200_Program_AddPlayWindow( hObj , (WORD)rcWins[0].left, (WORD)rcWins[0].top, (WORD)(rcWins[0].right - rcWins[0].left), (WORD)(rcWins[0].bottom - rcWins[0].top) );
			if ( nWndNo >= 0)
			{
				CP5200_Program_SetWindowProperty( hObj , nWndNo , 0x30 , 1 ); //
				//
				CString strText;
            	GetDlgItemText( IDC_EDIT_TEXT , strText );
				if (CP5200_Program_AddText(hObj, nWndNo, strText, 16, 0xFF, 0xFFFF, 100, 3 ) >= 0)
					nItemCnt++;
			}
	
			//
			nWndNo = CP5200_Program_AddPlayWindow( hObj , (WORD)rcWins[1].left, (WORD)rcWins[1].top, (WORD)(rcWins[1].right - rcWins[1].left), (WORD)(rcWins[1].bottom - rcWins[1].top) );
			if ( nWndNo >= 0)
			{
				//
				CString strText;
				GetDlgItemText( IDC_EDIT_PICT , strText );
				if (CP5200_Program_AddPicture(hObj,nWndNo, strText, 2, 0xFFFF, 100, 3, 0) >= 0)
					nItemCnt++;
			}

			if ( nItemCnt > 0 && CP5200_Program_SaveToFile( hObj, GetProgramFileName()) >= 0 )
					bRet = TRUE;
		}
		CP5200_Program_Destroy( hObj);
	}
    
	if ( bRet )
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");	
}

void CPower_VCDlg::OnBtnMakePlaybill() 
{
	UpdateData();
	BOOL bRet = FALSE;
	HOBJECT hObj = CP5200_Playbill_Create( m_nWidth, m_nHeight, 0x77 );
	if ( hObj)
	{		
		if ( CP5200_Playbill_AddFile( hObj, GetProgramFileName()) >= 0)
		{
			if ( CP5200_Playbill_SaveToFile( hObj, GetPlaybillFileName()) == 0)
				bRet = TRUE;
		}	
		CP5200_Playbill_Destroy(hObj);
	}

	if ( bRet )
		AfxMessageBox("Successful");
	else
		AfxMessageBox("Failed");
}

void CPower_VCDlg::OnBtnUpload() 
{
	UpdateData();
	InitComm();

	int nUploadCnt = 0 ;
	if ( m_nCommType == 1) //
	{
		if ( 0 == CP5200_Net_UploadFile( m_cmbCardID.GetCurSel()+1, GetProgramFileName(), GetProgramFileName()) )
			nUploadCnt++;

		if ( 0 == CP5200_Net_UploadFile( m_cmbCardID.GetCurSel()+1, GetPlaybillFileName(), GetPlaybillFileName()) )
			nUploadCnt++;

		if ( nUploadCnt > 0)
			CP5200_Net_RestartApp( m_cmbCardID.GetCurSel()+1 );
	}
	else //
	{
		if ( 0 == CP5200_RS232_UploadFile( m_cmbCardID.GetCurSel()+1, GetProgramFileName(), GetProgramFileName()) )
			nUploadCnt++;
		
		if ( 0 == CP5200_RS232_UploadFile( m_cmbCardID.GetCurSel()+1, GetPlaybillFileName(), GetPlaybillFileName()) )
			nUploadCnt++;

		if ( nUploadCnt > 0)
			CP5200_RS232_RestartApp( m_cmbCardID.GetCurSel()+1 );
	}

	CString strMag;
	strMag.Format("Upload 2 files , %d successful , %d failed !" , nUploadCnt , 2 - nUploadCnt );
	AfxMessageBox(strMag);	
}

