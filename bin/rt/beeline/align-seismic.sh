#!/bin/sh
# Copyright (c) 2004 The Regents of the University of California
# All Rights Reserved
# 
# Permission to use, copy, modify and distribute any part of this software for
# educational, research and non-profit purposes, without fee, and without a
# written agreement is hereby granted, provided that the above copyright
# notice, this paragraph and the following three paragraphs appear in all
# copies.
# 
# Those desiring to incorporate this software into commercial products or use
# for commercial purposes should contact the Technology Transfer Office,
# University of California, San Diego, 9500 Gilman Drive, La Jolla, CA
# 92093-0910, Ph: (858) 534-5815.
# 
# IN NO EVENT SHALL THE UNIVESITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
# LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF THE UNIVERSITY
# OF CALIFORNIA HAS BEEN ADIVSED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# THE SOFTWARE PROVIDED HEREIN IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
# CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
# ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF CALIFORNIA MAKES NO
# REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY KIND, EITHER IMPLIED OR
# EXPRESS, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT THE USE OF THE
# SOFTWARE WILL NOT INFRINGE ANY PATENT, TRADEMARK OR OTHER RIGHTS.
#
#   This code was created as part of the ROADNet project.
#   See http://roadnet.ucsd.edu/ 
#
#   Written By: Todd Hansen 7/26/2004
#   Updated By: Todd Hansen 7/26/2004


echo align-seismic $Revision: 1.1 $
echo
echo Please connect the GPS to port /dev/ttyS3 and turn it on.
echo Please place the GPS in a good position and mount the gyro to it.
echo Please connect the VG700CA Gyro to port /dev/ttyS4 and turn it on.
echo Ready? Please enter the station name followed by a "<CR>"
read sta;
echo "Starting GPS alignment tool (beeline)";
beeline /dev/ttyS3 GPSlog.$sta verbose
echo
echo GPS alignment finished, starting Gyro calibration
echo
echo "Please align the gyro with True North per the GPS offset (hit <CR> when done)"
read c
VG700CA -v -p /dev/ttyS4 -l Gyrolog.$sta
echo Alignment finished. log files: Gyrolog.$sta and GPSlog.$sta

