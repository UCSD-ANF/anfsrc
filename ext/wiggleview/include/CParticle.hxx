#ifndef _CPARTICLE_HXX
#define _CPARTICLE_HXX

#include "common.hxx"

class CParticle
{
public:

	CParticle();

	CParticle(float**, float**, float**, long);

	~CParticle();

	void update();

//	void update(CChannel*, CChannel*

	void reset();

	SoLineSet* getLineSet();

	SoPointSet* getPointSet();

	SoCoordinate3* getCoordsPointSet();

	SoCoordinate3* getCoordsLineSet();

	SoSeparator* getParticleSep();

	void setDiffuseColor(float, float , float);

	void setRotation(char, float);

	void increaseScale(float);
	
	void stop();

	void start();

	SbBool isStopped();

	void setGoodLocalScale(float );

	void setScale(SbVec3f);

	void setScale(SbVec3f, SbVec3f, SbVec3f);

	void setDelta(float);

	void createSubSetPoints(float);

	void next();

	void previous();

	void addDataToParticle(string,vector<int>);

	SbVec3f getHeadTrans();

protected:

	float m_speed;

	long m_numofPointsRead;

	long m_numOfPointsInPointSet;

	long m_counter;

	float** m_points;

	SbBool m_stop;

	SoPointSet *m_pointSet;

	SoLineSet *m_lineSet;

	SoCoordinate3 *m_coordsPointSet;

	SoCoordinate3 *m_coordsLineSet;

	SoSeparator *m_particleSep;

	SoScale *m_scale;

	SoTranslation *m_trans;

	SoRotation *m_rot;

	SoMaterial *m_mat;

	float m_goodLocalScale;

	SbBool m_useSubSet;
	float m_subSetNum;
	float m_delta;

	SoTranslation *m_headTrans;

	SbBool m_holdFinal;

	float m_stretchAmplitude;

	void init();
};

#endif
