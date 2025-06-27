// CPower_VCDlg.h : header file
//

#if !defined(AFX_CPower_VCDLG_H__26105604_CE6B_4E0B_A535_18A095B46623__INCLUDED_)
#define AFX_CPower_VCDLG_H__26105604_CE6B_4E0B_A535_18A095B46623__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

/////////////////////////////////////////////////////////////////////////////
// CPower_VCDlg dialog

class CPower_VCDlg : public CDialog
{
// Construction
public:
	CPower_VCDlg(CWnd* pParent = NULL);	// standard constructor

// Dialog Data
	//{{AFX_DATA(CPower_VCDlg)
	enum { IDD = IDD_CPOWER_VC_DIALOG };
	
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CPower_VCDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	//}}AFX_VIRTUAL

// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	//{{AFX_MSG(CPower_VCDlg)
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	virtual void OnOK();
	afx_msg void OnBtnMakeProgram();
	afx_msg void OnBtnMakePlaybill();
	afx_msg void OnBtnUpload();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
afx_msg void OnBnClickedRadio1();
	afx_msg void OnBnClickedRadio2();
	afx_msg void OnBnClickedBtnSplitWnd();
	afx_msg void OnBnClickedBtnSendText();
	afx_msg void OnBnClickedBtnSendPict();
	afx_msg void OnBnClickedBtnSendStaticText();
	afx_msg void OnBnClickedSendClock();
	afx_msg void OnBnClickedBtnSetTime();
	afx_msg void OnBnClickedBtnPlayProgram();

private:
	void InitComm(); //
	void EnableCtrl() ;
	void GetSplitWnd( RECT* rcWins );

	CString GetProgramFileName();
	CString GetPlaybillFileName();

private:
	int m_nCommType;

	CComboBox m_cmbPort;
	CComboBox m_cmbBaudrate;
	CComboBox m_cmbCardID;
    CIPAddressCtrl	m_ctrlIPAddr;
	CIPAddressCtrl	m_ctrlIDCode;
	int m_nPort;
	int m_nTimeOut;
	int m_nWidth;
	int m_nHeight;
	CComboBox m_cmbWndNo;
	int m_nProNo;
	
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_CPower_VCDLG_H__26105604_CE6B_4E0B_A535_18A095B46623__INCLUDED_)
