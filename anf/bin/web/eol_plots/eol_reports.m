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

cd([getenv('ANTELOPE') '/data/matlab/R2015a/antelope/scripts/']);

setup_antelope; 

cd(currentFolder);




mychan = [ 'BHZ', 'BHE', 'BHN' ] ;
%imgdir = '/anf/web/vhosts/anf.ucsd.edu/htdocs/cacheimages/eolplots' ;
imgdir = '/Users/reyes/repos/anfsrc/anf/bin/web/eol_plots/eolplots' ;

ev_database = '/anf/shared/dbcentral/dbcentral' ;
ev_clustername = 'usarray' ;


%event_list = containers.Map()
event_list = struct() ;


% Verify station value
if exist('cmd_station')
    mysta = eval('cmd_station') ;
else
    error('No station defined.') ;
end

% Verify lat value
if exist('cmd_lat')
    my_lat = eval('cmd_lat') ;
else
    error('No latitude defined.') ;
end

% Verify lon value
if exist('cmd_lon')
    my_lon = eval('cmd_lon') ;
else
    error('No longitude defined.') ;
end



dbs = dbcentral( '/anf/shared/dbcentral/dbcentral', 'usarray' ) ;
event_count = 0 ;


%--- Loop over dbcentral structure
%db = '/anf/TA/dbs/event_dbs/2014_10/usarray_2014_10'
%for db = dbs.databases'
db = '/anf/TA/dbs/event_dbs/2015_10/usarray_2015_10'

    %--- Verify value of database path
    if isempty( db )
        continue
    end

    %--- START: Database operations to get what we want

    fprintf( 'START: Database pull on %s\n', db ) ;

    db0 = dbopen( db, 'r' ) ;

    assoc = dblookup_table( db0,'assoc' ) ;
    arrival = dblookup_table( db0,'arrival' ) ;
    origin = dblookup_table( db0,'origin' ) ;
    event = dblookup_table( db0,'event' ) ;
    netmag = dblookup_table( db0,'netmag' ) ;

    db1 = dbsubset( assoc, ['sta =="' mysta '"'] ) ;
    db2 = dbjoin( db1, arrival ) ;

    db3 = dbsubset( db2, ['arrival.chan =~ /.*Z.*/'] ) ;

    db4 = dbjoin( db3, origin ) ;
    db5 = dbjoin( db4, event ) ;
    db6 = dbsubset( db5, ['orid == prefor'] ) ;
    db7 = dbjoin( db6,netmag ) ;

    nrecs = dbquery( db7,'dbRECORD_COUNT' ) ;

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

            %event_list(i+1)
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

%end

fprintf( 'Got [%d] events\n', event_count ) ;

    %events(m).readabletime = strtime( oridtime ) ;
    %[ split, pieces ] = explode( events(m).readabletime, ' ' ) ;
    %events(m).mmddyyyy = split(1) ;
    %events(m).HHMMSS = split(2) ;
    %clear split, pieces ;

    %%--- X-axis label
    %xlabel( ['Time from origin time (in minutes)' ] ) ;

    %%--- Title

    %%--- mytitle = { 
    %%---    [ 'Three components recorded from a ' events(m).type ' event detected by station' ] ;...
    %%---    [ mysta ' on ' events(m).readabletime ' UTC. The magnitude of this event was ' events(m).ev_mag ] ;...
    %%---    ['This event was located at ' sprintf( '%0.5g', events(m).ev_lat ) ' latitude and ' sprintf( '%0.5g', events(m).ev_lon ) ' longitude.' ] ;...
    %%---    ['Map opposite shows the event location (white star) and the station location (red triangle).' ] ...
    %%--- } ; 

    %%--- Get the output parameter file
    %if exist( eventinfopf ) == 0 
    %    pfinfo = dbpf() ;
    %else 
    %    pfinfo = dbpf( eventinfopf ) ;
    %end

    %mypftitle = [ events(m).type '_wform_plot' ] ;

    %%---- mytitle = { 
    %%----    [ 'Three components recorded from a ' events(m).type ' event detected by station TA_' mysta ' on ' events(m).readabletime ' UTC. The magnitude of this event was ' events(m).ev_mag '. This event was located at ' sprintf( '%0.5g', events(m).ev_lat ) ' latitude and ' sprintf( '%0.5g', events(m).ev_lon ) ' longitude and was approximately ' events(m).distance ' km from the recording station. The first seismic waves arrived ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
    %%---- } ; 

    %if( strcmp( events(m).type, 'regional' ) )
    %    pfput( pfinfo, 'regional_wform_eventnumber', events(m).ev_mag ) ;
    %    pfput( pfinfo, 'regional_wform_mmddyyyy', events(m).mmddyyyy ) ;
    %    pfput( pfinfo, 'regional_wform_hhmmss', events(m).HHMMSS ) ;
    %    pfput( pfinfo, 'regional_wform_distance', events(m).distance ) ;
    %    pfput( pfinfo, 'regional_wform_delay', sprintf( '%0.3g', events(m).delay ) ) ;
%
%   %     mytitle = { 
%   %         [ 'Three components recorded from the magnitude ' num2str( events(m).ev_mag ) ' regional event detected by station TA_' mysta ' on ' events(m).mmddyyyy ' (' events(m).HHMMSS ' UTC). This occurred approximately ' events(m).distance ' km from the station. The first seismic waves (P waves) arrived at this station ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
%   %     } ; 
    %else
    %    pfput( pfinfo, 'large_wform_eventnumber', events(m).ev_mag ) ;
    %    pfput( pfinfo, 'large_wform_mmddyyyy', events(m).mmddyyyy ) ;
    %    pfput( pfinfo, 'large_wform_hhmmss', events(m).HHMMSS ) ;
    %    pfput( pfinfo, 'large_wform_distance', events(m).distance ) ;
    %    pfput( pfinfo, 'large_wform_delay', sprintf( '%0.3g', events(m).delay ) ) ;
%   %     mytitle = { 
%   %         [ 'Three components recorded from a large event detected by station TA_' mysta ' on ' events(m).mmddyyyy ' (' events(m).HHMMSS ' UTC). The magnitude of this event was ' events(m).ev_mag ', and was approximately ' events(m).distance ' km from the recording station. The first seismic waves arrived at this station ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
%   %     } ; 
    %end

    %%--- axes('position',[ .05,.05,.9,.9 ] ) ; 
    %%--- htext = text( .5, 0.1, mytitle, 'FontSize',14 ) ; 
    %%--- set( htext, 'HorizontalAlignment','center' ) ; 
    %%--- set( gca, 'Visible','off' ) ;

%   % pfput( pfinfo, mypftitle, mytitle ) ;

    %%--- Write the parameter file object out
    %pfwrite( pfinfo, eventinfopf ) ;

    %%--- Free up memory
    %pffree( pfinfo ) ;
    %trdestroy( tr ) ;
    %dbclose( db ) ;

    %%--- Print to a file
    %%--- set(gcf, 'inverthardcopy', 'off');
    %figname = [ imgdir mysta '_' events(m).type '.eps' ] ;
    %print( '-depsc2',figname ) ;
    %% printstr = [ 'print -dpng -r72 ' figname ];
    %% eval( printstr ) ;

%end

%clear('reset') ;

%--- Run the complete events map generation part
fprintf( 'Run genevents(regional)\n') ;
%genevents( mysta, 'regional', event_list, my_lat, my_lon, imgdir )
fprintf( 'Run genevents(large)\n') ;
%genevents( mysta, 'large', event_list, my_lat, my_lon, imgdir )

fprintf( 'Run genmaps(regional)\n') ;
genmaps( mysta, 'regional', event_list, my_lat, my_lon, imgdir) ;
fprintf( 'Run genmaps(large)\n') ;
genmaps( mysta, 'large', event_list, my_lat, my_lon, imgdir) ;

fprintf( 'Run roseplots()\n') ;
%roseplots( mysta, event_list, my_lat, my_lon, imgdir) ;



%for m=1:length(events)
%    %--- Run the event specific map generation part
%    %genmaps( mysta, events(m).readabletime, events(m).ev_mag, events(m).type, mysta_lat, mysta_lon, events(m).ev_lat, events(m).ev_lon, imgdir, eventinfopf ) ;
%    %--- Run the complete events map generation part
%    %genevents( mysta, events(m).type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) ;
%    %--- Run the complete events rose and histogram plots
%    %roseplots( mysta, events(m).type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) ;
%end
%
%%clear('reset') ;
%
%exit
