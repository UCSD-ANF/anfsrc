% --------------------------------------------------------------------------------------------------
% Driver script for sensor_comparison.m
% --------------------------------------------------------------------------------------------------
function sensor_comparison_driver();

clear all;

global MINIMUM_MAGNITUDE MAX_EPICENTRAL_DIST WEAK_MOTION_PRECEDENCE STRONG_MOTION_PRECEDENCE ERROR_LOG NOW;

NETWORK = 'ANZA';

WEAK_MOTION_PRECEDENCE = {'BH.','HH.'}; %low to high
STRONG_MOTION_PRECEDENCE = {'BN.','HN.'}; %low to high

NOW = datestr(now,'yyyymmdd');

ERROR_LOG = fopen(sprintf('/anf/%s/work/white/xcal/%s/error_log',NETWORK,NOW),'a');

completed_dbs = fopen(sprintf('/anf/%s/work/white/xcal/%s/completed_dbs',NETWORK,datestr(now,'yyyymmdd')),'a');
fprintf(completed_dbs,'Successfully completed dbs\n==========================\n');

% time_bounds (seconds before, after predicted first arrival):
tb = [10 60];

if regexp(NETWORK,'^TA$')
    MINIMUM_MAGNITUDE = 5.0;
    MAX_EPICENTRAL_DIST = 2.0;
	event_dbs = {'2004_04','2004_05','2004_06','2004_07','2004_08','2004_09','2004_10','2004_11','2004_12','2005_01','2005_02','2005_03','2005_04','2005_05','2005_06','2005_07','2005_08','2005_09','2005_10','2005_11','2005_12','2006_01','2006_02','2006_03','2006_04','2006_05','2006_06','2006_07','2006_08','2006_09','2006_10','2006_11','2006_12','2007_01','2007_02','2007_03','2007_04','2007_05','2007_06','2007_07','2007_08','2007_09','2007_10','2007_11','2007_12','2008_01','2008_02','2008_03','2008_04','2008_05','2008_06','2008_07','2008_08','2008_09','2008_10','2008_11','2008_12','2009_01','2009_02','2009_03','2009_04','2009_05','2009_06','2009_07','2009_08','2009_09','2009_10','2009_11','2009_12','2010_01','2010_02','2010_03','2010_04','2010_05','2010_06','2010_07','2010_08','2010_09','2010_10','2010_11','2010_12','2011_01','2011_02','2011_03','2011_04','2011_05','2011_06','2011_07','2011_08','2011_09','2011_10','2011_11','2011_12','2012_01','2012_02','2012_03','2012_04','2012_05','2012_06','2012_07','2012_08','2012_09','2012_10','2012_11','2012_12','2013_01','2013_02','2013_03','2013_04','2013_05','2013_06','2013_07'};
    %event_dbs = {'2010_07'};
elseif regexp(NETWORK,'^ANZA$')
    MINIMUM_MAGNITUDE = 3.0;
    MAX_EPICENTRAL_DIST = 1.0;
    event_dbs = {'anza','anza_2012','anza_pre2012'};
    %event_dbs = {'2007','2008','2009'};
end

for i=1:length(event_dbs)
    
    event_db = event_dbs{1,i};
    
    if regexp(NETWORK,'^TA$')
        dbpath = sprintf('/anf/TA/dbs/event_dbs/%s/usarray_%s',event_db,event_db);
    elseif regexp(NETWORK,'^ANZA$')
        dbpath = sprintf('/anf/ANZA/rt/anza/%s',event_db);
        %dbpath = sprintf('/anf/ANZA/dbs/event_dbs/%s/anza_%s',event_db,event_db);
    else
        disp('Invalid network.');
        break;
    end
    
    events = get_event_subset(dbpath);
    
    if length(events) > 0

        disp(sprintf('Processing event db - %s',event_db));

        for j=1:length(events)
            
            prefor = sprintf('%.0f',events(j));
            disp(sprintf('\tProcessing orid - %s',prefor));
            proximal_stas = get_proximal_stas(dbpath,prefor);

            for k=1:length(proximal_stas)

                sta = proximal_stas{1,k};
                
                if has_colocated_sensors(dbpath,prefor,sta)
                    
                    weak_chan = get_precedent_weak(dbpath,prefor,sta);
                    strong_chan = get_precedent_strong(dbpath,prefor,sta);
                    ptt = first_arrival_travel_time(dbpath,prefor,sta);
                    
                    disp(sprintf('\t\tPerforming sensor comparison for %s %s %s',sta,weak_chan,strong_chan));
                    tic;
                    sensor_comparison(dbpath, NETWORK, prefor, sta, [-ptt+tb(1) ptt+tb(2)], strong_chan, weak_chan);
                    toc;
                    
                else
                end
            end
        end
        fprintf(completed_dbs,'%s\n',dbpath);
    end
end

fclose(ERROR_LOG);
   
%--------------------------------------------------------------------------

function [events] = get_event_subset(dbpath);
global MINIMUM_MAGNITUDE;

db = dbopen(dbpath,'r');

dbe = dblookup_table(db,'event');
dbe = dbjoin(dbe,dblookup_table(db,'origin'));
dbe = dbsubset(dbe,'orid == prefor');

events = [];

if dbnrecs(dbjoin(dbe,dblookup_table(db,'netmag'))) == 0
    dbe = dbsubset(dbe,sprintf('mb >= %f || ml >= %f || ms >= %f',MINIMUM_MAGNITUDE,MINIMUM_MAGNITUDE,MINIMUM_MAGNITUDE));
    dbe = dbsort(dbe,'time');
    events = dbgetv('prefor');
else
    dbe = dbjoin(dbe,dblookup_table(db,'netmag'));
    dbe = dbsubset(dbe,sprintf('magnitude >= %f',MINIMUM_MAGNITUDE));
    dbe = dbsever(dbe,'netmag');
    if dbnrecs(dbe) > 0
        dbe = dbsort(dbe,'time');
        events = dbgetv(dbe,'prefor');
    end
end
dbclose(db);

%--------------------------------------------------------------------------

function [proximal_stas] = get_proximal_stas(dbpath,prefor);
global MAX_EPICENTRAL_DIST;
db = dbopen(dbpath,'r');

dbo = dblookup_table(db,'origin');
dbo = dbsubset(dbo, sprintf('orid == %s',prefor));
dbo = dbjoin(dbo,dblookup_table(db,'site'));
dbo.record = 0;

proximal_stas = {};

for i=0:dbnrecs(dbo)-1
    dbo.record = i;
    
    if dbeval(dbo,'distance(lat,lon,site.lat,site.lon)') < MAX_EPICENTRAL_DIST
        proximal_stas{length(proximal_stas)+1} = dbgetv(dbo,'sta');
    end
end
dbclose(db);

%--------------------------------------------------------------------------
function [return_bool] = has_colocated_sensors(dbpath,prefor,sta);
global STRONG_MOTION_PRECEDENCE WEAK_MOTION_PRECEDENCE;
db = dbopen(dbpath,'r');

dbo = dblookup_table(db,'origin');
dbo = dbsubset(dbo, sprintf('orid == %s',prefor));
dbo = dbsubset(dbjoin(dbo,dblookup_table(db,'sitechan')),sprintf('sta =~ /%s/',sta));

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
    if dbfind(dbo,str_s) ~= -102
        has_strong = true;
    end

    if dbfind(dbo,str_w) ~= -102
        has_weak = true;
    end
catch err
end
    
if has_weak && has_strong
    return_bool = true;
end
dbclose(db);

%--------------------------------------------------------------------------

function [strong_precedent] = get_precedent_strong(dbpath,prefor,sta);
global STRONG_MOTION_PRECEDENCE;
db = dbopen(dbpath,'r');

dbo = dblookup_table(db,'origin');
dbo = dbsubset(dbo, sprintf('orid == %s',prefor));
dbo = dbsubset(dbjoin(dbo,dblookup_table(db,'sitechan')),sprintf('sta =~ /%s/',sta));

for i=1:length(STRONG_MOTION_PRECEDENCE)
    if dbfind(dbo,sprintf('chan =~ /%s/',STRONG_MOTION_PRECEDENCE{1,i})) ~= -102
        strong_precedent = STRONG_MOTION_PRECEDENCE{1,i};
    end
end
dbclose(db);

%--------------------------------------------------------------------------
function [weak_precedent] = get_precedent_weak(dbpath,prefor,sta);
global WEAK_MOTION_PRECEDENCE;
db = dbopen(dbpath,'r');

dbo = dblookup_table(db,'origin');
dbo = dbsubset(dbo, sprintf('orid == %s',prefor));
dbo = dbsubset(dbjoin(dbo,dblookup_table(db,'sitechan')),sprintf('sta =~ /%s/',sta));

for i=1:length(WEAK_MOTION_PRECEDENCE)
    if dbfind(dbo,sprintf('chan =~ /%s/',WEAK_MOTION_PRECEDENCE{1,i})) ~= -102
        weak_precedent = WEAK_MOTION_PRECEDENCE{1,i};
    end
end
dbclose(db);

%--------------------------------------------------------------------------    
function [ptt] = first_arrival_travel_time(dbpath,prefor,sta);
db = dbopen(dbpath,'r');

dbo = dblookup_table(db,'origin');
dbo = dbsubset(dbo, sprintf('orid == %s',prefor));
dbo = dbjoin(dbo,dblookup_table(db,'site'));
dbo.record = dbfind(dbo,sprintf('sta =~ /%s/',sta));
ptt = dbeval(dbo,'deg2km(distance(lat,lon,site.lat,site.lon))') / 6; %assume p-wave velocity of 5 km/s
dbclose(db);

