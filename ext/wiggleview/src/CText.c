
#include "CText.hxx"

CText::CText()
{}


CText::CText(string str)
{
	initCText();
}

CText::CText(vector<string> vec)
{
	initCText();
	for(int i = 0 ; i < vec.size(); i++)
	{
		SoAsciiText *someText= new SoAsciiText;
		someText->string = vec[i].c_str();
		//someText->width = 0;
		m_blinker->addChild(someText);
	}
	
}


CText::~CText()
{}


void CText::initCText()
{
	m_annotation  = new SoAnnotation;
	m_annotation->ref();
	m_switch      = new SoSwitch;
	m_blinker     = new SoBlinker;
	m_translation = new SoTranslation;
	m_scale		  = new SoScale;


	m_annotation->addChild(m_translation);
	m_annotation->addChild(m_scale);
	m_annotation->addChild(m_switch);

	m_switch->addChild(m_blinker);
	
	m_switch->whichChild = 0;
	
	m_blinker->whichChild = 0;
	m_blinker->on = TRUE;
	//m_blinker->speed = 1.0f;


}


void CText::normalize(const SbViewportRegion &region)
{
	// Normalizing each object
	SoGetBoundingBoxAction bboxAction(region);
	bboxAction.apply(m_annotation);
	SbBox3f bbox = bboxAction.getBoundingBox();
	float xsize, ysize, zsize, scaleFactor;
	bbox.getSize(xsize, ysize, zsize);
	
	if (xsize > ysize)
		if (xsize > zsize)
			scaleFactor = xsize;
		else
			scaleFactor = zsize;
	else
		if (ysize > zsize)
			scaleFactor = ysize;
		else
			scaleFactor = zsize;
	scaleFactor = 1.0f / scaleFactor;
//	SbVec3f rep;
//	rep = bboxAction.getCenter();
//	rep = -rep;
//	SoTransform *animTransform = new SoTransform;

//	animTransform->translation.setValue(rep);
	m_scale->scaleFactor.setValue(SbVec3f(scaleFactor,scaleFactor, scaleFactor));
	//return animTransform;
	//setPosition(-250,-250,0);
}

void CText::setPosition(float x, float y, float z)
{
	m_translation->translation.setValue(x,y,z);
}

void CText::setScale(float x, float y, float z)
{
	m_scale->scaleFactor.setValue(SbVec3f(x,y, z));
}

/*
void CText::hide()
{
	m_switch->whichChild = SO_SWITCH_NONE;
}

void CText::show()
{
	m_switch->whichChild = 0;
}

SbBool CText::isHidden()
{
	if (m_switch->whichChild.getValue() == SO_SWITCH_NONE)
		return TRUE;
	else
		return FALSE;
}

*/

SoAnnotation* CText::getAnnotation()
{
	return m_annotation;
}

SoBlinker* CText::getBlinker()
{
	return m_blinker;
}

void CText::toggleDisplay()
{
#ifdef DEBUG
	cout<<"Currently text display is "<<m_switch->whichChild.getValue()<<endl;
#endif
	if (m_switch->whichChild.getValue() == SO_SWITCH_NONE)
		m_switch->whichChild = 0;
	else
		m_switch->whichChild = SO_SWITCH_NONE;
#ifdef DEBUG
	if (m_blinker->on.getValue() == TRUE)
		cout<<"Text blinker is ON"<<endl;
	else
		cout<<"Text blinker is OFF"<<endl;
	cout<<"Child no displayed "<<m_blinker->whichChild.getValue()<<endl;
#endif
}
