#include "CTimeTick.h"

CTimeTick::CTimeTick()
{
	init();
}

CTimeTick::CTimeTick(string str, float xTrans, float yTrans, float zTrans)
{
	init();
	m_timeTickText->string.setValue(str.c_str());
	m_timeTickTrans->translation.setValue(xTrans, yTrans, zTrans);	

}

CTimeTick::~CTimeTick()
{

}

void CTimeTick::updateTimeText(string str)
{
	m_timeTickText->string.setValue(str.c_str());
}

void CTimeTick::init()
{
	m_timeTickSep = new SoSeparator;
	m_timeTickText = new SoText2;
	m_timeTickTrans = new SoTranslation;
	m_timeTickSep->addChild(m_timeTickTrans);
	m_timeTickSep->addChild(m_timeTickText);
	
}
