#include <CSeismogram.hxx>

CSeismogram::CSeismogram()
{
	
}

CSeismogram::~CSeismogram()
{}

void CSeismogram::setLatitude(float& val)
{
	m_latitude = val;
}

void CSeismogram::setLongitude(float& val)
{
	m_longitude = val;
}

void CSeismogram::setFrequency(float& val)
{
	m_frequency = val;
}

void CSeismogram::addAmplitudeValues(int * vals, int & num)
{
	for (int i = 0; i < num; i++)
		m_amplitude.push_back(vals[i]);
}

float CSeismogram::getLatitude()
{
	return m_latitude;
}

float CSeismogram::getLongitude()
{
	return m_longitude;
}

float CSeismogram::getFrequency()
{
	return m_frequency;
}

vector<int> CSeismogram::getAmplitudeValues()
{
	return m_amplitude;
}
