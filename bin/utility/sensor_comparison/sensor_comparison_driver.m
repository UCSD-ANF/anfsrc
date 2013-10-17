function sensor_comparison_driver();
% --------------------------------------------------------------------------------------------------
% Driver script for sensor_comparison.m
% --------------------------------------------------------------------------------------------------

clear all;

global MINIMUM_MAGNITUDE MAX_EPICENTRAL_DIST WEAK_MOTION_PRECEDENCE STRONG_MOTION_PRECEDENCE NETLESS_STATIONS;

%WEAK_MOTION_PRECEDENCE = {'LH.','BH.','HH.'}; %low to high
%STRONG_MOTION_PRECEDENCE = {'LN.','BN.','HN.'}; %low to high
WEAK_MOTION_PRECEDENCE = {'BH.','HH.'}; %low to high
STRONG_MOTION_PRECEDENCE = {'BN.','HN.'}; %low to high

% time_bounds (seconds before, after predicted first arrival):
%tb = [1000 4500];
tb = [10 60];

NETWORK = 'ANZA';

if regexp(NETWORK,'^TA$')
    MINIMUM_MAGNITUDE = 5.0;
    MAX_EPICENTRAL_DIST = 2.0;
	%event_dbs = {'2004_04','2004_05','2004_06','2004_07','2004_08','2004_09','2004_10','2004_11','2004_12','2005_01','2005_02','2005_03','2005_04','2005_05','2005_06','2005_07','2005_08','2005_09','2005_10','2005_11','2005_12','2006_01','2006_02','2006_03','2006_04','2006_05','2006_06','2006_07','2006_08','2006_09','2006_10','2006_11','2006_12','2007_01','2007_02','2007_03','2007_04','2007_05','2007_06','2007_07','2007_08','2007_09','2007_10','2007_11','2007_12','2008_01','2008_02','2008_03','2008_04','2008_05','2008_06','2008_07','2008_08','2008_09','2008_10','2008_11','2008_12','2009_01','2009_02','2009_03','2009_04','2009_05','2009_06','2009_07','2009_08','2009_09','2009_10','2009_11','2009_12','2010_01','2010_02','2010_03','2010_04','2010_05','2010_06','2010_07','2010_08','2010_09','2010_10','2010_11','2010_12','2011_01','2011_02','2011_03','2011_04','2011_05','2011_06','2011_07','2011_08','2011_09','2011_10','2011_11','2011_12','2012_01','2012_02','2012_03','2012_04','2012_05','2012_06','2012_07','2012_08','2012_09','2012_10','2012_11','2012_12','2013_01','2013_02','2013_03','2013_04','2013_05','2013_06','2013_07'};
    event_dbs = {'2013_05'};
    %event_dbs = {'2010_07'};
elseif regexp(NETWORK,'^ANZA$')
    MINIMUM_MAGNITUDE = 3.0;
    MAX_EPICENTRAL_DIST = 1.0;
    event_dbs = {'anza','anza_2012','anza_pre2012'};
end

for i=1:length(event_dbs)
    event_db = event_dbs{1,i};
    if regexp(NETWORK,'^TA$')
        dbpath = sprintf('/anf/TA/dbs/event_dbs/%s/usarray_%s',event_db,event_db);
    elseif regexp(NETWORK,'^ANZA$')
        dbpath = sprintf('/anf/ANZA/rt/anza/%s',event_db);
    else
        disp('Invalid network.');
        break;
    end
    
    db = dbopen(dbpath,'r');
    
    %NETLESS_STATIONS = dbgetv(dbnojoin(dblookup_table(db,'site'),dblookup_table(db,'snetsta')),'sta');

    db_events = dblookup_table(db,'event');
    db_events = dbjoin(db_events,dblookup_table(db,'origin'));
    db_events = dbsubset(db_events,'orid == prefor');
    db_events = dbjoin(db_events,dblookup_table(db,'netmag'));
    db_events = dbsubset(db_events,sprintf('magnitude >= %f',MINIMUM_MAGNITUDE));
    db_events = dbsever(db_events,'netmag');
    db_events = dbsort(db_events,'time');

    disp(sprintf('Processing event db - %s',event_db));
    
    for j=0:dbnrecs(db_events)-1
        db_events.record=j;
        prefor = dbgetv(db_events,'prefor');
        disp(sprintf('\tProcessing orid - %d',prefor));
        
        db_origin = dblookup_table(db,'origin');
        db_origin = dbsubset(db_origin, sprintf('orid == %d',prefor));
        db_origin.record = 0;
        proximal_stas = get_proximal_stas(db_origin);
        
        for k=1:length(proximal_stas)
            db_sta = dbsubset(dbjoin(db_origin,dblookup_table(db_origin,'sitechan')),sprintf('sta =~ /%s/',proximal_stas{1,k}));
            db_sta.record = 0;

            if has_colocated_sensors(db_sta)
                weak_chan = get_precedent_weak(db_sta);
                strong_chan = get_precedent_strong(db_sta);
                station = dbgetv(db_sta,'sta');
                ptt = first_arrival_travel_time(db_sta);
                disp(sprintf('\t\tPerforming sensor comparison for %s %s %s',station,weak_chan,strong_chan));
                %disp(sprintf('\t\tsensor_comparison_v2(%s, %d, %s, [%d %d], %s, %s, [%d %d], %d)',dbpath,prefor,station,-ptt-tb(1),ptt+tb(2),strong_chan,weak_chan));
                tic;
                sensor_comparison(db, NETWORK, prefor, station, [-ptt+tb(1) ptt+tb(2)], strong_chan, weak_chan);
                toc;
                %input('Press enter to continue...');
            end
            dbfree(db_sta);
        end
        dbfree(db_origin);
    end
    dbfree(db_events);
    dbclose(db);
end
   
%--------------------------------------------------------------------------
function [proximal_stas] = get_proximal_stas(db);
global MAX_EPICENTRAL_DIST;
dbptr = dbjoin(db,dblookup_table(db,'site'));
dbptr.record = 0;

proximal_stas = {};

for i=0:dbnrecs(dbptr)-1
    dbptr.record = i;
    
    if dbeval(dbptr,'distance(lat,lon,site.lat,site.lon)') < MAX_EPICENTRAL_DIST
        proximal_stas{length(proximal_stas)+1} = dbgetv(dbptr,'sta');
    end
end
dbfree(dbptr);

%--------------------------------------------------------------------------
function [return_bool] = has_colocated_sensors(db);
global STRONG_MOTION_PRECEDENCE WEAK_MOTION_PRECEDENCE;

has_weak = false;
has_strong = false;
return_bool = false;

str_s = sprintf('chan =~ /%s/',STRONG_MOTION_PRECEDENCE{1,1});
for i=2:length(STRONG_MOTION_PRECEDENCE)
    str_s = sprintf( '%s || chan =~ /%s/',str_s,STRONG_MOTION_PRECEDENCE{1,i});
end

str_w = sprintf('chan =~ /%s/',WEAK_MOTION_PRECEDENCE{1,1});
for i=2:length(WEAK_MOTION_PRECEDENCE)
    str_w = sprintf( '%s || chan =~ /%s/',str_w,WEAK_MOTION_PRECEDENCE{1,i});
end
try
    if dbfind(db,str_s) ~= -102
        has_strong = true;
    end

    if dbfind(db,str_w) ~= -102
        has_weak = true;
    end
catch err
end
    
if has_weak && has_strong
    return_bool = true;
end

%--------------------------------------------------------------------------

function [strong_precedent] = get_precedent_strong(dbptr);
global STRONG_MOTION_PRECEDENCE;
for i=1:length(STRONG_MOTION_PRECEDENCE)
    if dbfind(dbptr,sprintf('chan =~ /%s/',STRONG_MOTION_PRECEDENCE{1,i})) ~= -102
    %if dbnrecs(dbsubset(dbptr,sprintf('chan =~ /%s/',STRONG_MOTION_PRECEDENCE{1,i}))) > 0
        strong_precedent = STRONG_MOTION_PRECEDENCE{1,i};
    end
end

%--------------------------------------------------------------------------
function [weak_precedent] = get_precedent_weak(dbptr);
global WEAK_MOTION_PRECEDENCE;
for i=1:length(WEAK_MOTION_PRECEDENCE)
    if dbfind(dbptr,sprintf('chan =~ /%s/',WEAK_MOTION_PRECEDENCE{1,i})) ~= -102
    %if dbnrecs(dbsubset(dbptr,sprintf('chan =~ /%s/',WEAK_MOTION_PRECEDENCE{1,i}))) > 0
        weak_precedent = WEAK_MOTION_PRECEDENCE{1,i};
    end
end

%--------------------------------------------------------------------------    
function [ptt] = first_arrival_travel_time(db);
%dbptr = dbsubset(dbjoin(dbptr,dblookup_table(dbptr,'site')),'sta == site.sta');
%dbptr.record = 0;
dbptr = dbjoin(db,dblookup_table(db,'site'));
dbptr.record = dbfind(dbptr,'sta == site.sta');
ptt = dbeval(dbptr,'deg2km(distance(lat,lon,site.lat,site.lon))') / 6; %assume p-wave velocity of 5 km/s
dbfree(dbptr);

