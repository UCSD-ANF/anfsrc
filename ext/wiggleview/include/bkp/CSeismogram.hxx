#ifndef _CSEISMOGRAM_HXX
#define _CSEISMOGRAM_HXX

#include <vector>
#include <map>
#include <string>
using namespace std;

class CSeismogram 
{
	public :
		CSeismogram();
		~CSeismogram();
		void setLatitude(float &);
		void setLongitude(float &);
		void addAmplitudeValues(int*,int&);
		void setFrequency(float &);
		float getLatitude();
		float getLongitude();
		float getFrequency();
		vector<int> getAmplitudeValues();

	protected :
		vector<int> m_amplitude;
		float 	    m_latitude;
		float 	    m_longitude;
		float       m_frequency;
		void init();

};

#endif
