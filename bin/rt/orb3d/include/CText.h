/******************************************************************
 * ImmersaView
 * Copyright (C) 2003 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Chris Scharver, Vikas Chowdhry, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/
#ifndef _CTEXT_HXX
#define _CTEXT_HXX
#pragma warning(disable:4275)
#pragma warning(disable:4251)
#include "common.h"

class CText
{
public:

	CText();
	CText(string);
	~CText();
	CText(vector<string>);
	void init(vector<string>);
	void setPosition(float, float, float);
	void setScale(float);
	void setScale(float, float, float);
	void normalize(const SbViewportRegion&);
	//void hide();
	//void show();
	//SbBool isHidden();
	void toggleDisplay();
	SoAnnotation* getAnnotation();
	SoBlinker* getBlinker();
private:
	void init();
	SoAnnotation  *m_annotation;
	SoSwitch      *m_switch;
	SoBlinker     *m_blinker;
	SoTranslation *m_translation;
	SoScale       *m_scale;

};

#endif

