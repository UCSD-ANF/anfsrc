#ifndef _CTEXT_HXX
#define _CTEXT_HXX
//#pragma warning(disable:4275)
//#pragma warning(disable:4251)
#include "common.hxx"

class CText
{
public:

	CText();
	CText(string);
	~CText();
	CText(vector<string>);
	//void init(vector<string>);
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
	void initCText();
	SoAnnotation  *m_annotation;
	SoSwitch      *m_switch;
	SoBlinker     *m_blinker;
	SoTranslation *m_translation;
	SoScale       *m_scale;

};

#endif

