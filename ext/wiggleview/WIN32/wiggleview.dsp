# Microsoft Developer Studio Project File - Name="wiggleview" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Console Application" 0x0103

CFG=wiggleview - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "wiggleview.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "wiggleview.mak" CFG="wiggleview - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "wiggleview - Win32 Release" (based on "Win32 (x86) Console Application")
!MESSAGE "wiggleview - Win32 Debug" (based on "Win32 (x86) Console Application")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
RSC=rc.exe

!IF  "$(CFG)" == "wiggleview - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD CPP /nologo /MT /W3 /GX /O2 /I "../include" /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /D "COIN_DLL" /D "SIMAGE_DLL" /D "QUANTA_DO_NOT_USE_GLOBUS" /D "QUANTA_LITTLE_ENDIAN" /D "QUANTA_THREAD_SAFE" /D "QUANTA_USE_PTHREADS" /YX /FD /c
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib coin1.lib simage1.lib glut32.lib quanta.lib ws2_32.lib pthread.lib /nologo /subsystem:console /machine:I386

!ELSEIF  "$(CFG)" == "wiggleview - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /GZ /c
# ADD CPP /nologo /W3 /Gm /GX /ZI /Od /I "../include" /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /D "COIN_DLL" /D "SIMAGE_DLL" /D "QUANTA_DO_NOT_USE_GLOBUS" /D "QUANTA_LITTLE_ENDIAN" /D "QUANTA_THREAD_SAFE" /D "QUANTA_USE_PTHREADS" /YX /FD /GZ /c
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib coin1d.lib simage1.lib glut32.lib quanta.lib ws2_32.lib pthread.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept

!ENDIF 

# Begin Target

# Name "wiggleview - Win32 Release"
# Name "wiggleview - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=..\src\CAnimConfig.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CAnimControl.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CChannel.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CParticle.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CSearch.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CSeismogram.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CSeismometer.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CServer.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CText.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CTimer.cxx
# End Source File
# Begin Source File

SOURCE=..\src\CUtil.cxx
# End Source File
# Begin Source File

SOURCE=..\src\wiggleview.cxx
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl"
# Begin Source File

SOURCE=..\include\CAnimConfig.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CAnimControl.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CChannel.hxx
# End Source File
# Begin Source File

SOURCE=..\include\common.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CParticle.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CSearch.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CSeismogram.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CSeismometer.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CServer.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CText.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CTimer.hxx
# End Source File
# Begin Source File

SOURCE=..\include\CUtil.hxx
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
# End Group
# Begin Source File

SOURCE=..\data\wilber\AnzaConfig.iv
# End Source File
# Begin Source File

SOURCE=..\configFiles\StereoCameras.iv
# End Source File
# Begin Source File

SOURCE=..\data\wilber\TurkeyConfig.iv
# End Source File
# End Target
# End Project
