<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
    <!ENTITY raquo 	"&#x000BB;">
    <!ENTITY sep 	" ">
]>
<xsl:stylesheet version="2.0" 
    xmlns="http://earth.google.com/kml/2.2" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema">

    <!-- <xsl:output method="xml" indent="yes" cdata-section-elements="description" /> -->
    <xsl:output method="xml" indent="no" cdata-section-elements="description" />

    <!-- {{{ Define variables -->
    <xsl:variable name="lcletters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
    <xsl:variable name="ucletters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>
    <xsl:variable name="iconpath">http://anf.ucsd.edu/images/icons/google_earth/</xsl:variable>
    <xsl:variable name="sneticonpath"><xsl:value-of select="$iconpath" />snet/</xsl:variable>
    <xsl:variable name="currentdatetime"><xsl:value-of select="current-dateTime()"/></xsl:variable>
    <xsl:variable name="currentyear"><xsl:value-of select="year-from-dateTime($currentdatetime)"/></xsl:variable>
    <!-- }}} Define variables -->

    <!-- {{{ KML output -->

    <xsl:template match="/">
        <kml xmlns="http://www.opengis.net/kml/2.2">

            <NetworkLinkControl>
                <expires><xsl:value-of select="xs:dateTime($currentdatetime) + xs:dayTimeDuration('P1D')" /></expires>
            </NetworkLinkControl>

            <!-- {{{ Document -->

            <Document>
                <name>ANF EarthScope USArray Broadband Seismic Station Deployment Interface</name>
                <TimeStamp><xsl:value-of select="$currentdatetime"/></TimeStamp>
                <Schema parent="Placemark" name="USArray_Station" />
                <open>1</open>
                <description>The Array Network Facility (ANF) EarthScope USArray broadband seismic station deployment interface.  This GE layer displays the location and metadata of broadband seismic stations in the USArray project, with accompanying station photographs. Spatial and temporal station changes are plotted over time, allowing viewers to observe the seismic network evolution.</description>
                <LookAt>
                    <longitude>-100</longitude>
                    <latitude>40</latitude>
                    <altitude>0</altitude>
                    <range>4000000</range>
                    <tilt>0</tilt>
                    <heading>0</heading>
                </LookAt>
                <ScreenOverlay>
                    <name>ANF title image</name>
                    <Icon>
                        <href><xsl:value-of select="$iconpath" />anf_title_ge.png</href>
                    </Icon>
                    <overlayXY x="0" y="0.02" xunits="fraction" yunits="fraction"/>
                    <screenXY x="0" y="0.02" xunits="fraction" yunits="fraction"/>
                    <rotationXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
                    <size x="-1" y="-1" xunits="pixels" yunits="pixels"/>
                </ScreenOverlay>

                <!-- {{{ Styles -->

                <xsl:for-each select="distinct-values( document('/anf/web/vhosts/anf.ucsd.edu/htdocs/cachexml/stations/sio_google_layer_detail.xml')/station_list/stations/station/Network )">
                    <Style id="stationIcon{.}">
                        <ListStyle>
                            <ItemIcon>
                                <href><xsl:value-of select="$sneticonpath" /><xsl:value-of select="." />.png</href>
                            </ItemIcon>
                        </ListStyle>
                        <BalloonStyle>
                            <bgColor>ffffffff</bgColor>
                            <textColor>ff000000</textColor>
                            <text>$[description]</text>
                        </BalloonStyle>
                        <IconStyle>
                            <Icon>
                                <href><xsl:value-of select="$sneticonpath" /><xsl:value-of select="." />.png</href>
                            </Icon>
                            <x>24</x>
                            <w>24</w>
                            <h>24</h>
                        </IconStyle>
                    </Style>
                    <Style id="stationIcon{.}_offline">
                        <BalloonStyle>
                            <bgColor>ffffffff</bgColor>
                            <textColor>ff000000</textColor>
                            <text>$[description]</text>
                        </BalloonStyle>
                        <IconStyle>
                            <Icon>
                                <href><xsl:value-of select="$sneticonpath" /><xsl:value-of select="." />_offline.png</href>
                            </Icon>
                            <x>38</x>
                            <w>38</w>
                            <h>38</h>
                        </IconStyle>
                    </Style>
                </xsl:for-each>

                <!-- }}} Styles -->

                <xsl:for-each select="document('/anf/web/vhosts/anf.ucsd.edu/htdocs/cachexml/stations/sio_google_layer_detail.xml')/station_list/snets/snet">
                    <xsl:variable name="idval" select="@id" />

                   <!-- {{{ Folder output -->

                    <Folder id="{$idval}">

                        <name><xsl:value-of select="." /></name>
                        <styleUrl>#stationIcon<xsl:value-of select="$idval" /></styleUrl>

                        <xsl:for-each select="../../stations/station[Network=$idval]">
                            <xsl:variable name="thisSnet"><xsl:value-of select="$idval" /></xsl:variable>
                            <xsl:variable name="iconSnet"><xsl:value-of select="$sneticonpath" /><xsl:value-of select="Network" />.png</xsl:variable>
                            <xsl:variable name="thisSnetSta"><xsl:value-of select="Network" />_<xsl:value-of select="@name" /></xsl:variable>
                            <xsl:variable name="moreinfo">http://anf.ucsd.edu/stations/<xsl:value-of select="$thisSnet" />/<xsl:value-of select="@name" /></xsl:variable>

                           <!-- {{{ Placemark output -->

                            <Placemark id="{$thisSnetSta}">
                                <name><xsl:value-of select="@name" /></name>
                                <Snippet maxLines="0"></Snippet>
                                <styleUrl>#stationIcon<xsl:value-of select="Network" /></styleUrl>
                                <TimeSpan>
                                    <begin><xsl:value-of select="TimeSpan/begin" /></begin>
                                        <xsl:if test="TimeSpan/end">
                                            <end><xsl:value-of select="TimeSpan/end" /></end>
                                        </xsl:if>
                                </TimeSpan>
                                <Point>
                                    <coordinates><xsl:value-of select="Longitude" />,<xsl:value-of select="Latitude" />,0</coordinates>
                                </Point>

                                <description>
                                    <xsl:text disable-output-escaping="yes">&lt;![CDATA[</xsl:text>           

<!-- {{{ Content of the Balloon -->

<div id="test" style="margin:0;padding:0;float:right;background-image:">
    <img src="{$iconSnet}" />
</div>
<h1 style="font-size:20px;"><xsl:value-of select="Network" />:<xsl:value-of select="@name"/></h1>
<table id="metadata" style="border:1px solid #333;width:100%;padding:3px;margin:0 auto;clear:both;">
    <caption style="width:100%;margin:0 auto;padding:5px;background-color:#900;color:white;font-weight:bold;border:1px solid #333;border-bottom:none;font-size:16px">Broadband Seismic Station Metadata</caption>
    <xsl:for-each select="*">
        <xsl:choose>
            <xsl:when test="name(.) = 'topPickPhoto'">
            </xsl:when>
            <xsl:when test="contains(name(.),'TimeSpan')">
            </xsl:when>
            <xsl:otherwise>
            <!-- <xsl:if test="not(contains(name(.),'topPickPhoto')) or not(contains(name(.),'TimeSpan'))"> -->
                <tr>
                    <td style="background-color:#8B7355;font-weight:bold;border:1px solid #333;color:white;font-size:16px">

                    <xsl:choose>
                        <xsl:when test="contains(name(.),'_')">
                            <xsl:value-of select="substring-before(name(.), '_')" /><xsl:text> </xsl:text><xsl:value-of select="substring-after(name(.), '_')" />
                        </xsl:when>
                        <xsl:otherwise>
                                <xsl:value-of select="name()" />
                        </xsl:otherwise>
                    </xsl:choose>

                    </td>
                    <td style="border:1px solid #333;background-color:#FFF;color:black;font-size:16px">
                        <xsl:value-of select="." />
                    </td>
                </tr>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:for-each>
</table>

<xsl:if test="topPickPhoto">
    <xsl:variable name="photo"><xsl:value-of select="topPickPhoto" /></xsl:variable>
    <img style="border:1px solid #333;padding:3px;margin:0 auto;margin-top:10px;" src="http://anf.ucsd.edu/cacheimages/station_photos/{$photo}"  />
</xsl:if>

<p><a href="{$moreinfo}">More information &sep;&raquo;&sep;</a></p>
<p>&#169; <xsl:value-of select="$currentyear"/> Array Network Facility, http://anf.ucsd.edu</p>

<!-- }}} Content of the Balloon -->

                                    <xsl:text disable-output-escaping="yes">]]</xsl:text>
                                    <xsl:text disable-output-escaping="yes">&gt;</xsl:text>
                                </description>

                            </Placemark>

                           <!-- }}} Placemark output -->

                        </xsl:for-each>

                    </Folder>

                   <!-- }}} Folder output -->

                </xsl:for-each>

            </Document>

            <!-- }}} Document -->

        </kml>

    </xsl:template>

    <!-- }}} KML output -->

</xsl:stylesheet>
