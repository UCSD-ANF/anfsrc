%-----------------------------------------------------
%  Get events into MatLab and display plots
%-----------------------------------------------------
%
% A Matlab script for retrieving and displaying
% waveform data from regional and teleseismic event
% databases using settings from a PHP dynamically 
% generated parameter file (eol_report_runtime.pf)
%
% Requires genmaps.m 
%
% @category  Datascope
% @package   Matlab
% @author    Rob Newman <rlnewman@ucsd.edu>
% @copyright Copyright (c) 2007 UCSD
% @license   MIT-style license
% @version   1.0
%
% v1.2 2011-04-27
% v1.1 2008-01-24
%
%-----------------------------------------------------

%--- START: Open up dynamically generated parameter file

fprintf( 'Start Matlab interpreter\n' ) ;

fprintf( 'START: Parse parameter file eol_report_runtime\n' ) ;

% path
% eol_report_runtime.pf

if exist( 'eol_report_runtime.pf' ) == 0 
    fprintf( 'Fatal error: Parameter file eol_report_runtime does not exist\n' ) ;
    exit
end

% New setup for Antelope bindings. See JIRA ticket # WWW-91 
% https://anf.ucsd.edu/jira/browse/WWW-91
addpath(getenv('ANTELOPE'))
setup

pf = dbpf( 'eol_report_runtime.pf' ) ;

glo_db_loc = pfget_string( pf, 'dbs_global' ) ;
reg_db_loc = pfget_string( pf, 'dbs_regional' ) ;
imgdir = pfget_string( pf, 'wvform_image_dir' ) ;
ev_database = pfget_string( pf, 'ev_database' ) ;

events(1).type = 'regional' ;
events(1).myorid = pfget_string( pf, 'ev_reg_orid' ) ;
events(1).mytime = pfget( pf, 'ev_reg_time' ) ;
events(1).mywindow = pfget( pf, 'ev_reg_window' ) ;
events(1).mydb = pfget_string( pf, 'dbs_regional' ) ;
events(1).lead = pfget( pf, 'ev_reg_lead' ) ;
events(1).ev_lat = pfget( pf, 'ev_reg_lat' ) ;
events(1).ev_lon = pfget( pf, 'ev_reg_lon' ) ;
events(1).ev_mag = pfget_string( pf, 'ev_reg_mag' ) ;
events(1).distance = pfget_string( pf, 'ev_reg_distance' ) ;

events(2).type = 'large' ;
events(2).myorid = pfget_string( pf, 'ev_glo_orid' ) ;
events(2).mytime = pfget( pf, 'ev_glo_time' ) ;
events(2).mywindow = pfget( pf, 'ev_glo_window' ) ;
events(2).mydb = pfget_string( pf, 'dbs_global' ) ;
events(2).lead = pfget( pf, 'ev_glo_lead' ) ;
events(2).ev_lat = pfget( pf, 'ev_glo_lat' ) ;
events(2).ev_lon = pfget( pf, 'ev_glo_lon' ) ;
events(2).ev_mag = pfget_string( pf, 'ev_glo_mag' ) ;
events(2).distance = pfget_string( pf, 'ev_glo_distance' ) ;

mysta = pfget_string( pf, 'sta_code' ) ;
mysta_lat = pfget( pf, 'sta_lat' ) ;
mysta_lon = pfget( pf, 'sta_lon' ) ;
mychan = pfget_string( pf, 'sta_chans' ) ;
imgdir = pfget_string( pf, 'wvform_image_dir' ) ;
eventinfopf = pfget_string( pf, 'eventinfopf' ) ;
fprintf( 'END: Parse parameter file eol_report_runtime\n' ) ;

%--- END: Open up dynamically generated parameter file

%--- Loop over structure (Matlab's associative array)
for m=1:length(events)

    %--- Add control structure to only run script if vars are set
    if isempty( events(m).myorid ) 
        continue
    end

    %--- START: Database operations to get what we want

    fprintf( 'START: Database operations\n' ) ;

    db = dbopen( events(m).mydb,'r' ) ;

    dbas = dblookup_table( db,'assoc' ) ;
    dbar = dblookup_table( db,'arrival' ) ;
    dbor = dblookup_table( db,'origin' ) ;
    dbwf = dblookup_table( db,'wfdisc' ) ;

    dbj1 = dbjoin(dbas, dbar);
    naras = dbquery(dbj1, 'dbRECORD_COUNT') ;

    dbj1 = dbjoin(dbj1, dbor);    
    narasor = dbquery(dbj1, 'dbRECORD_COUNT') ;

    dbj1 = dbjoin(dbj1, dbwf);
    naraswf = dbquery(dbj1, 'dbRECORD_COUNT') ;

    %--- Get an origin
    dbj1 = dbsubset( dbj1, ['orid=="' events(m).myorid '"'] ) ;

    dbj1.record = 0 ;
    oridtime = dbgetv( dbj1, 'origin.time' ) ;

    fprintf( 'END: Database operations\n' ) ;

    %--- Open the wfdisc
    dbj1 = dbsubset( dbj1, ['sta=="' mysta '"'] ) ;
    dbj1 = dbsubset( dbj1, ['chan=~/' mychan '/'] ) ;

    joinednrecs = dbquery( dbj1, 'dbRECORD_COUNT' ) ;

    arrivals = dbseparate(dbj1, 'arrival') ;
    arrnrecs = dbquery( arrivals, 'dbRECORD_COUNT' ) ;

    %--- Need to ensure we have a complete section, 
    %--- not just the wfdisc entries containing the orid
    %--- wforms = dbseparate(dbj1, 'wfdisc') ;
    %--- wforms = dbsubset( wforms, ['chan=~/' mychan '/'] ) ;

    try
        [ arr_time, arr_chan, arr_iphase ] = dbgetv( arrivals, 'arrival.time', 'chan', 'iphase' ) ;
    catch
        fprintf( 'Cannot get arrival time, arrival channel or arrival phase, killing Matlab interpreter\n' ) ;
        exit
    end
    %%%--- sprintf( '%0.5g', ( arr_time - oridtime ) ) 

    %--- START: Get the first arrival
    arrivals.record = 0 ;
    try
        [ first_arr_time ] = dbgetv( arrivals, 'arrival.time' ) ;
    catch
        fprintf( 'Cannot get arrival time, killing Matlab interpreter\n' ) ;
        exit
    end

    events(m).delay = ( first_arr_time - oridtime ) ;
    %--- END: Get the first arrival

    arr_time_mins = ( arr_time - oridtime ) / 60 ;

    t0 = arr_time(1) - events(m).lead ;
    t1 = t0 + events(m).mywindow ;

    %--- Go back to using the original wfdisc
    dbwf = dbsubset( dbwf, ['chan=~/' mychan '/'] ) ;
    t0_ant = sprintf( '%17.5f', t0 ) ;
    t1_ant = sprintf( '%17.5f', t1 ) ;
    dbwf = dbsubset( dbwf, ['endtime > ' t0_ant ' && time < ' t1_ant ] ) ;

    try
        tr = trload_css( dbwf, t0, t1 ) ;
    catch
        fprintf( 'Cannot load trace object data, killing Matlab interpreter\n' ) ;
        exit
    end 
    trapply_calib( tr ) ;
    trsplice( tr,0.5) ;
    nrecs = dbquery( tr,'dbRECORD_COUNT' ) ;

    %--- END: Database operations to get what we want

    %--- Set up bkgrd and frgrd colors
    figure('Visible','off') ;
    clf ;

    % whitebg( [ 0 0 .63 ] ) ;
    whitebg( [ 1 1 1 ] ) ;
    % set( gcf, 'Color', [ 0, 0, 0 ] ) ;
    set( gcf, 'Color', [ 1, 1, 1 ] ) ;
    % set( gca, 'Color', 'y' ) ;
    set( gca, 'Color', 'b' ) ;

    set( gcf, 'PaperUnits', 'inches' ) ;
    set( gcf, 'PaperOrientation', 'portrait' ) ;
    set( gcf, 'PaperSize', [ 7 5 ] ) ;
    set( gcf, 'PaperType', 'B2' ) ;

    %--- Use to determine max and min for plots
    for i=1:nrecs,
        tr.record = i-1;
        data_for_y = trextract_data(tr) ;
        data_for_y = data_for_y - ( sum( data_for_y ) / length( data_for_y ) ) ;
        max_y(i) = max( abs( data_for_y ) ) ;
    end

    my_max_y = max( abs( max_y ) ) ;
    my_min_y = my_max_y * -1 ;

    pl_min = [ 0.05 0.05 ] ;
    pl_max = [ 0.98 0.98 ] ;
    pl_gap = [ 0.01 0.01 ] ;

    Xmin = pl_min(1) ;
    Ymin = pl_min(2) ;
    Xmax = pl_max(1) ;
    Ymax = pl_max(2) ;
    Xgap = pl_gap(1) ;
    Ygap = pl_gap(2) ;

    Xsize =	( Xmax - Xmin ) ;
    Ysize =	( Ymax - Ymin ) ;

    Xbox = Xsize - Xgap ;
    Ybox = Xsize - Ygap ;

    %--- Default to zero so we can do a test. Can't get exist() to work
    new_height = 0 ;

    for i=1:nrecs,

        h = subplot( nrecs,1,i ) ;

        tr.record = i-1;
        data = trextract_data(tr) ;
        data = data - ( sum( data ) / length( data ) ) ;

        xtime = 1/(dbgetv(tr,'samprate'))*[1:length(data)];		

        %--- Get data in mins from orid time
        xtimeo = ( t0 + xtime - oridtime ) / 60 ;

        plot(xtimeo,data) ;

        set( h, 'YLim', [ my_min_y my_max_y ] ) ;

        this_pos = get( h, 'Position' ) ;

        new_pos(1) = Xmin ;
        new_pos(2) = this_pos(2) + ( 0.07 * i ) ;
        new_pos(3) = Xsize ;

        if new_height == 0
            new_pos(4) = this_pos(4) ;
            new_height = new_pos(4) ;
        else
            new_pos(4) = new_height ;
        end

        set( h, 'Position', [ new_pos(1) new_pos(2) new_pos(3) new_pos(4) ] ) ;

        hold on ;

        %--- Only add time stamp on last (bottom) wform display
        if i < nrecs
            set( gca, 'XTickLabel', [] ) ;
        end

        set( gca, 'xtick', [] ) ;
        set( gca, 'xgrid', 'on' ) ;

        yy = get(gca,'ylim') ;

        grid2 on x off y ;
        mylabel = dbgetv( tr, 'chan' ) ;
        ylabel( mylabel, 'FontSize', 12 ) ;
        set( gca,'yticklabel',[] ) ;
        set( gca, 'xtickMode', 'auto' ) ;

        %--- Offset so text is readable
        dy = 0.025*(yy(2)-yy(1)) ;

        for a=1:length( arr_time_mins ),
            %--- Hack to solve Matlab casting of strings and cells
            if length( arr_time_mins ) == 1
                this_chan = arr_chan ;
                this_iphase = arr_iphase ;
            else
                this_chan = arr_chan(a) ;
                this_iphase = arr_iphase(a) ;
            end

            if( strcmp( mylabel, this_chan ) )
                plot([arr_time_mins(a) arr_time_mins(a)],yy,'LineWidth', 1, 'Color', [ .6 0 0 ]) ;
                text( [arr_time_mins(a)], yy(2)-dy,this_iphase,...
                    'HorizontalAlignment','left',...
                    'VerticalAlignment','top',...
                    'BackgroundColor', [ 1 0 0 ],...
                    'FontWeight', 'bold',...
                    'EdgeColor', [ .6 0 0 ] ) ;
            end
        end

    end

    events(m).readabletime = strtime( oridtime ) ;
    [ split, pieces ] = explode( events(m).readabletime, ' ' ) ;
    events(m).mmddyyyy = split(1) ;
    events(m).HHMMSS = split(2) ;
    clear split, pieces ;

    %--- X-axis label
    xlabel( ['Time from origin time (in minutes)' ] ) ;

    %--- Title

    %--- mytitle = { 
    %---    [ 'Three components recorded from a ' events(m).type ' event detected by station' ] ;...
    %---    [ mysta ' on ' events(m).readabletime ' UTC. The magnitude of this event was ' events(m).ev_mag ] ;...
    %---    ['This event was located at ' sprintf( '%0.5g', events(m).ev_lat ) ' latitude and ' sprintf( '%0.5g', events(m).ev_lon ) ' longitude.' ] ;...
    %---    ['Map opposite shows the event location (white star) and the station location (red triangle).' ] ...
    %--- } ; 

    %--- Get the output parameter file
    if exist( eventinfopf ) == 0 
        pfinfo = dbpf() ;
    else 
        pfinfo = dbpf( eventinfopf ) ;
    end

    mypftitle = [ events(m).type '_wform_plot' ] ;

    %---- mytitle = { 
    %----    [ 'Three components recorded from a ' events(m).type ' event detected by station TA_' mysta ' on ' events(m).readabletime ' UTC. The magnitude of this event was ' events(m).ev_mag '. This event was located at ' sprintf( '%0.5g', events(m).ev_lat ) ' latitude and ' sprintf( '%0.5g', events(m).ev_lon ) ' longitude and was approximately ' events(m).distance ' km from the recording station. The first seismic waves arrived ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
    %---- } ; 

    if( strcmp( events(m).type, 'regional' ) )
        pfput( pfinfo, 'regional_wform_eventnumber', events(m).ev_mag ) ;
        pfput( pfinfo, 'regional_wform_mmddyyyy', events(m).mmddyyyy ) ;
        pfput( pfinfo, 'regional_wform_hhmmss', events(m).HHMMSS ) ;
        pfput( pfinfo, 'regional_wform_distance', events(m).distance ) ;
        pfput( pfinfo, 'regional_wform_delay', sprintf( '%0.3g', events(m).delay ) ) ;
%
%        mytitle = { 
%            [ 'Three components recorded from the magnitude ' num2str( events(m).ev_mag ) ' regional event detected by station TA_' mysta ' on ' events(m).mmddyyyy ' (' events(m).HHMMSS ' UTC). This occurred approximately ' events(m).distance ' km from the station. The first seismic waves (P waves) arrived at this station ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
%        } ; 
    else
        pfput( pfinfo, 'large_wform_eventnumber', events(m).ev_mag ) ;
        pfput( pfinfo, 'large_wform_mmddyyyy', events(m).mmddyyyy ) ;
        pfput( pfinfo, 'large_wform_hhmmss', events(m).HHMMSS ) ;
        pfput( pfinfo, 'large_wform_distance', events(m).distance ) ;
        pfput( pfinfo, 'large_wform_delay', sprintf( '%0.3g', events(m).delay ) ) ;
%        mytitle = { 
%            [ 'Three components recorded from a large event detected by station TA_' mysta ' on ' events(m).mmddyyyy ' (' events(m).HHMMSS ' UTC). The magnitude of this event was ' events(m).ev_mag ', and was approximately ' events(m).distance ' km from the recording station. The first seismic waves arrived at this station ' sprintf( '%0.3g', events(m).delay ) ' seconds after the event occurred.' ] ...
%        } ; 
    end

    %--- axes('position',[ .05,.05,.9,.9 ] ) ; 
    %--- htext = text( .5, 0.1, mytitle, 'FontSize',14 ) ; 
    %--- set( htext, 'HorizontalAlignment','center' ) ; 
    %--- set( gca, 'Visible','off' ) ;

%    pfput( pfinfo, mypftitle, mytitle ) ;

    %--- Write the parameter file object out
    pfwrite( pfinfo, eventinfopf ) ;

    %--- Free up memory
    pffree( pfinfo ) ;
    trdestroy( tr ) ;
    dbclose( db ) ;

    %--- Print to a file
    %--- set(gcf, 'inverthardcopy', 'off');
    figname = [ imgdir mysta '_' events(m).type '.eps' ] ;
    print( '-depsc2',figname ) ;
    % printstr = [ 'print -dpng -r72 ' figname ];
    % eval( printstr ) ;

end

clear('reset') ;

for m=1:length(events)
    %--- Run the event specific map generation part
    genmaps( mysta, events(m).readabletime, events(m).ev_mag, events(m).type, mysta_lat, mysta_lon, events(m).ev_lat, events(m).ev_lon, imgdir, eventinfopf ) ;
    %--- Run the complete events map generation part
    genevents( mysta, events(m).type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) ;
    %--- Run the complete events rose and histogram plots
    roseplots( mysta, events(m).type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) ;
end

clear('reset') ;

exit
