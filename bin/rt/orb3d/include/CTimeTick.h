#ifndef _CTIME_TICK
#define _CTIME_TICK

#include "common.h"

class CTimeTick {

	public :
		CTimeTick();
		CTimeTick(string str, float xTrans, float yTrans, float zTrans);
		~CTimeTick();
		SoSeparator *m_timeTickSep;
		void updateTimeText(string str);	

	private :
		void init();
		SoText2*  m_timeTickText;
		SoTranslation* m_timeTickTrans;



};

#endif
