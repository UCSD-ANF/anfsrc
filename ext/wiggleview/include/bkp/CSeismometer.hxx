#ifndef _CSEISMOMETER_HXX
#define _CSEISMOMETER_HXX

#include "common.hxx"
#include "CChannel.hxx"
#include "CParticle.hxx"

class CSeismometer 
{
	public:
		
		CSeismometer();
		CSeismometer(string, int, SbBool);
		~CSeismometer();
		// param3 : how many points to display , decided by timer
		void update(float,SbBool,int);
		SoSeparator* getSep();
		void stretchTimeAxis(float);
		void stretchAmplitudeAxis(float);
		void toggleWiggles();
		void toggleParticle();
		void start();
		void stop();
		void next();
		void previous();
		void reset();
		void addChannel(CChannel*);
		SbBool isFinished();
		string getStationId();
		string getStationName();
		void addDataToChannel(string, string, string,
				float, float, float, vector<int>);
	protected:

		CChannel *bhz;
		CChannel *bhn;
		CChannel *bhe;
		CParticle *particle;
		SoSeparator *m_seismometerSep;
		SoScale *m_scale;
		SoTranslation *m_trans;
		SoRotation *m_rot;
		SoMaterial *m_mat;
		SoSwitch *m_particleSwitch;
		SoSwitch *m_wiggleSwitch;
		float m_startTime;
		SoText2 *m_stationText;
		string m_stationId;
		string m_stationName;
		void init();
		float m_angle;
		SbVec3f m_axis;
		float m_sphereTrans[3];
};

#endif
