%-----------------------------------------------------
%  Get events into MatLab and display plots
%-----------------------------------------------------
%
% A Matlab script for retrieving and displaying
% waveform data from regional and teleseismic events
%
%-----------------------------------------------------


fprintf( 'Start Matlab interpreter\n' ) ;

currentFolder = pwd;

setenv('ANTELOPE', '/opt/antelope/5.6');
setenv('ANF', '/opt/anf/5.6');

cd([getenv('ANTELOPE') '/data/matlab/R2015a/antelope/scripts/']);

setup_antelope;

% Avoid
%cd( currentFolder ) ;
%addpath([getenv('ANF') '/opt/anf/5.6/data/matlab']) ;

% Lets go to the folder itself.
cd( [getenv('ANF') '/opt/anf/5.6/data/matlab']) ;


event_list = struct() ;


% Verify image directory value
if exist('img_dir')
    global imgdir ;
    imgdir = eval('img_dir') ;
    fprintf( 'imgdir: %s\n', imgdir ) ;
else
    error('No imagedir defined.') ;
    exit( 1 );
end

% Verify dbcentral value
if exist('ev_database')
    ev_database = eval('ev_database') ;
    fprintf( 'ev_database: %s\n', ev_database ) ;
else
    error('No database defined.') ;
    exit( 1 );
end

% Verify dbcentral clustername value
if exist('ev_clustername')
    ev_clustername = eval('ev_clustername') ;
    fprintf( 'ev_clustername: %s\n', ev_clustername ) ;
else
    error('No dbcentral clustername defined.') ;
end

% Verify waveform database values
if exist('wf_database')
    wf_database = eval('wf_database') ;
    fprintf( 'wf_database: %s\n', wf_database ) ;
else
    error('No waveform database defined.') ;
    exit( 1 );
end

% Verify waveform dbcentral clustername value
if exist('wf_clustername')
    wf_clustername = eval('wf_clustername') ;
    fprintf( 'wf_clustername: %s\n', wf_clustername ) ;
else
    error('No waveform dbcentral clustername defined.') ;
end

% Verify TOPO maps folder
if exist('topomaps')
    global topomaps;
    topomaps = eval('topomaps') ;
    fprintf( 'topomaps: %s\n', topomaps ) ;
else
    error('No directory with topo data defined.') ;
    exit( 1 ) ;
end

% ImageMagic convert process
if exist('convert_exec')
    global CONVERT ;
    CONVERT = eval('convert_exec') ;
    fprintf( 'convert: %s\n', CONVERT ) ;
else
    error('No convert process identified.') ;
    exit( 1 ) ;
end


% Verify network value
if exist('net')
    mynet = eval('net') ;
    fprintf( 'mynet: %s\n', mynet ) ;
else
    error('No network defined.') ;
    exit( 1 ) ;
end

% Verify station value
if exist('sta')
    global station ;
    station = eval('sta') ;
    station = eval('sta') ;
    fprintf( 'station: %s\n', station ) ;
else
    error('No station defined.') ;
    exit( 1 ) ;
end

% Verify channels value
if exist('chans')
    global channels ;
    channels = eval('chans') ;
    fprintf( 'channels: %s\n',  strjoin(channels',', ') ) ;
else
    error('No channels defined.') ;
    exit( 1 ) ;
end

% Verify lat value
if exist('lat')
    global latitude ;
    latitude = eval('lat') ;
    my_lat = eval('lat') ;
    fprintf( 'my_lat: %s\n', my_lat ) ;
else
    error('No latitude defined.') ;
    exit( 1 ) ;
end

% Verify lon value
if exist('lon')
    global longitude ;
    longitude = eval('lon') ;
    my_lon = eval('lon') ;
    fprintf( 'my_lon: %s\n', my_lon ) ;
else
    error('No longitude defined.') ;
    exit( 1 );
end

% Verify time value
if exist('time')
    global sta_time ;
    sta_time = eval('time') ;
    fprintf( 'sta_time: %s\n', sta_time ) ;
else
    error('No time defined.') ;
    exit( 1 );
end
% Verify endtime value
if exist('endtime')
    global sta_endtime ;
    sta_endtime = eval('endtime') ;
    fprintf( 'sta_endtime: %s\n', sta_endtime ) ;
else
    error('No endtime defined.') ;
    exit( 1 );
end

if exist('ev_clustername')

    dbs = dbcentral( ev_database, ev_clustername, sta_time, sta_endtime ) ;

else
    dbs = [ ev_database ] ;
end

event_count = 0 ;

%--- Verify value of database object
if exist('dbs')
    fprintf( 'got %d databases\n', length(dbs.databases) ) ;
else
    error( 'ERROR IN dbcentral OBJECT %s[%s]\n', ev_database, ev_clustername ) ;
    exit( 1 );
end


%--- Loop over dbcentral structure
%db = '/anf/TA/dbs/event_dbs/2014_10/usarray_2014_10'
%db = '/anf/TA/dbs/event_dbs/2015_10/usarray_2015_10'
for c = 1:length(dbs.databases)

    %--- Verify value of database path
    if isempty( dbs.databases{c} )
        continue
    end

    %--- START: Database operations to get what we want

    fprintf( 'START: Database lookup on %s\n', dbs.databases{c} ) ;

    try
        db0 = dbopen( dbs.databases{c}, 'r' ) ;
        assoc = dblookup_table( db0,'assoc' ) ;
        arrival = dblookup_table( db0,'arrival' ) ;
        origin = dblookup_table( db0,'origin' ) ;
        event = dblookup_table( db0,'event' ) ;
        netmag = dblookup_table( db0,'netmag' ) ;

        db1 = dbsubset( assoc, ['sta =="' station '"'] ) ;
        db2 = dbjoin( db1, arrival ) ;

        db3 = dbsubset( db2, ['arrival.chan =~ /.*Z.*/'] ) ;

        db4 = dbjoin( db3, origin ) ;
        db5 = dbjoin( db4, event ) ;
        db6 = dbsubset( db5, ['orid == prefor'] ) ;
        db7 = dbjoin( db6,netmag ) ;

        nrecs = dbquery( db7,'dbRECORD_COUNT' ) ;
    catch
        fprintf( 'Problems with %s. SKIPPING.\n', db ) ;
        continue
    end


    fprintf( 'Got [%d] records\n', nrecs ) ;

    if nrecs < 1
        continue
    end

    for i=0:nrecs-1,

        db7.record = i ;

        event_count =  event_count + 1 ;

        try
            [ lat, lon, magtype, mag, seaz, delta, time, arrivaltime, phase ] = dbgetv( db7, 'origin.lat', 'origin.lon', 'netmag.magtype', 'netmag.magnitude', 'seaz', 'delta', 'origin.time', 'arrival.time', 'assoc.phase') ;
            event_list( event_count ).Lat = lat ;
            event_list( event_count ).Lon = lon ;
            event_list( event_count ).mag = mag ;
            event_list( event_count ).magtype = magtype ;
            event_list( event_count ).seaz = seaz ;
            event_list( event_count ).delta = delta ;
            event_list( event_count ).time = time ;
            event_list( event_count ).phase = phase ;
            event_list( event_count ).arrival = arrivaltime ;
            event_list( event_count ).Geometry = 'Point' ;
            event_list( event_count ).Cluster = ceil(mag) ;

        catch exception

            disp(exception.identifier) ;
            disp(exception) ;
            error( 'Cannot get event information.\n' ) ;
        end


    end

    dbfree( assoc )
    dbfree( arrival )
    dbfree( origin )
    dbfree( event )
    dbfree( netmag )

    dbfree( db1 )
    dbfree( db2 )
    dbfree( db3 )
    dbfree( db4 )
    dbfree( db5 )
    dbfree( db6 )
    dbfree( db7 )
    dbclose( db0 )

end

fprintf( 'Got [%d] events\n', event_count ) ;

if event_count < 1
    error( 'No events found in databases.' ) ;
    exit( 1 ) ;
else

    %--- Run the complete events map generation part
    fprintf( 'Run genevents(regional)\n') ;
    genevents( 'regional', event_list ) ;
    fprintf( 'Run genevents(large)\n') ;
    genevents( 'large', event_list ) ;

    fprintf( 'Run genmaps(regional)\n') ;
    genmaps( 'regional', event_list, ev_database, ev_clustername, wf_database, wf_clustername ) ;
    fprintf( 'Run genmaps(large)\n') ;
    genmaps( 'large', event_list, ev_database, ev_clustername, wf_database, wf_clustername ) ;

    fprintf( 'Run roseplots()\n') ;
    roseplots( event_list ) ;

end

clear all ;
clear classes ;


