#ifndef _CHANNEL_H
#define _CHANNEL_H

#include "common.h"
//#include "CSearch.h"

class CChannel
{
public:

	CChannel();
	
	CChannel(string channelId, float r, float g, float b);

	~CChannel();

	void reset();

	void next();

	void previous();

	void showAll();

	void stop();

	void start();

	SbBool isStopped();

	SoLineSet* getLineSet();

	SoPointSet* getPointSet();

	SoCoordinate3* getCoordsPointSet();

	SoCoordinate3* getCoordsLineSet();

	SoSeparator* getChannelSep();

	float** getPoints();

	long getNumPointsRead();

	void setDiffuseColor(float, float , float);

	void setRotation(char, float);

	void stretchTimeAxis(float);

	void stretchAmplitudeAxis(float);

	float getLatitude();

	float getLongitude();

	SbVec3f getScale();

	float getStartTime();

	void createSubSetPoints(float);

	SbBool isFinished();

	void addDataToChannel(string channelId,int numPts, float xUnit, float sampleRate, vector<float> pts, double currTime, double pktTime);

	void scrollTimeAxis(int shift);
	
	void setMinMaxAmplitude(float min, float max);

	double m_max_amplitude;
	double m_min_amplitude;
	double m_centerAmplitude;
	double m_unitAmplitude;
	double m_xUnit;

protected:

	//void init();

	string m_fileName;

	char m_timeAxis;
	
	char m_amplitudeAxis;
	
	float m_speed;
	
	long m_numofPointsRead;
	
	long m_numOfPointsInPointSet;

	long m_counter;

	string m_stationId;

	string m_stationName;

	// wrt
	string m_channelId;

	// wrt
	string m_siteId;

	float** m_points;

	float m_latitude;

	float m_longitude;

	float m_goodLocalScale;
	
	float m_stretchAmplitude;

	float m_stretchTime;
	
	string m_scaleType;

//	float m_points[5][3];

	SoPointSet *m_pointSet;

	SoLineSet *m_lineSet;

	SoCoordinate3 *m_coordsPointSet;

	SoCoordinate3 *m_coordsLineSet;

	SoSeparator *m_channelSep;

	SoScale *m_scale;

	SoTranslation *m_trans;

	SoRotation *m_rot;

	SoMaterial *m_mat;

	SbBool m_stop;

	//float m_startTime;
	double m_startTime;

	SbBool m_useSubSet;

	float m_subSetNum;

	float m_delta;

	string m_wiggleDir;

	SbBool m_holdFinal;

private :
	void init();
	void convertDataToScreenPoints(vector<float> in,
	vector<float> &screenPts,
	const float screenCenter);
	vector<float> dataPts;
/*	{
		m_channelSep = new SoSeparator;
		m_channelSep->ref();
		m_scale = new SoScale;
		m_trans = new SoTranslation;
		m_rot   = new SoRotation;
		m_mat = new SoMaterial;
		m_lineSet = new SoLineSet;
		m_coordsLineSet = new SoCoordinate3;
		SoLightModel *light = new SoLightModel;
		light->model = SoLightModel::BASE_COLOR;
		m_channelSep->addChild(m_scale);
		m_channelSep->addChild(m_trans);
		m_channelSep->addChild(m_rot);
		m_channelSep->addChild(m_mat);
		m_channelSep->addChild(m_coordsLineSet);
		m_channelSep->addChild(light);
		m_channelSep->addChild(m_lineSet);
	};
	*/
	
};

#endif
