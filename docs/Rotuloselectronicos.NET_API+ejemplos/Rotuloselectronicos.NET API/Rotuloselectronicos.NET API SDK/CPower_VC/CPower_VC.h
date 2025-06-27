// CPower_VC.h : main header file for the CPower_VC application
//

#if !defined(AFX_CPower_VC_H__9C213261_B782_43F2_80D8_A3781855E89F__INCLUDED_)
#define AFX_CPower_VC_H__9C213261_B782_43F2_80D8_A3781855E89F__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#ifndef __AFXWIN_H__
	#error include 'stdafx.h' before including this file for PCH
#endif

#include "resource.h"		// main symbols

/////////////////////////////////////////////////////////////////////////////
// CPower_VCApp:
// See CPower_VC.cpp for the implementation of this class
//

class CPower_VCApp : public CWinApp
{
public:
	CPower_VCApp();

// Overrides
	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CPower_VCApp)
	public:
	virtual BOOL InitInstance();
	//}}AFX_VIRTUAL

// Implementation

	//{{AFX_MSG(CPower_VCApp)
		// NOTE - the ClassWizard will add and remove member functions here.
		//    DO NOT EDIT what you see in these blocks of generated code !
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};


/////////////////////////////////////////////////////////////////////////////

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_CPower_VC_H__9C213261_B782_43F2_80D8_A3781855E89F__INCLUDED_)
