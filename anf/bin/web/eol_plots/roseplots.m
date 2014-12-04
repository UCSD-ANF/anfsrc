%-----------------------------------------------------
%  Plot roseplot of events for lifetime of the station
%-----------------------------------------------------
%
% A Matlab script for plotting events
%
% @category  Datascope
% @package   Matlab
% @author    Rob Newman <rlnewman@ucsd.edu>
% @copyright Copyright (c) 2009 UCSD
% @license   MIT-style license
% @version   1.0
%
% v1.0.1 2009-05-12
%
%-----------------------------------------------------

function roseplots( mysta, ev_type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) 

    %--- TEST CASE
    % mysta = 'BNLO' ;
    % ev_type = 'large' ;
    % ev_type = 'regional' ;
    % ev_database = '/tmp/eol_events_BNLO/BNLO_comp' ;
    % mysta_lat = 37.1311 ;
    % mysta_lon = -122.1729 ;
    % imgdir = '/anf/anfops1/usarray/plots/eol_representative_event_plots' ;

    %--- What defines the spacing in the graphs
    dc = 10 ;

    if exist( eventinfopf ) == 0 
        pfinfo = dbpf() ;
    else 
        pfinfo = dbpf( eventinfopf ) ;
    end

    %--- START: Database operations to get what we want
    db = dbopen( ev_database,'r' ) ;

    dbas = dblookup_table( db,'assoc' ) ;
    dbar = dblookup_table( db,'arrival' ) ;
    dbor = dblookup_table( db,'origin' ) ;
    dbev = dblookup_table( db,'event' ) ;

    dbj1 = dbjoin(dbas, dbar);
    naras = dbquery(dbj1, 'dbRECORD_COUNT') ;

    dbj1 = dbjoin(dbj1, dbor);    
    narasor = dbquery(dbj1, 'dbRECORD_COUNT') ;

    dbj1 = dbjoin(dbj1, dbev);

    %-- Now we can get what we want from the composite database created by dbcentral
    if( strcmp( ev_type, 'regional' ) )
        %--- This is for the regional map only
        range = 10 ;
        lat_min = mysta_lat - range ;
        lat_max = mysta_lat + range ;
        lon_min = mysta_lon - range ;
        lon_max = mysta_lon + range ;
        %--- Just retrieve one event per evid
        dbj1 = dbsort( dbj1, 'dbSORT_UNIQUE', 'evid' ) ;
        dbj1 = dbsubset( dbj1, '( delta < 10 )' ) ;
    else
        % dbj1 = dbsubset( dbj1, ['( mb >= 6.5 || ms >= 6.5 || ml >= 6.5 )'] ) ;
        dbj1 = dbsort( dbj1, 'dbSORT_UNIQUE', 'evid' ) ;
        dbj1 = dbsubset( dbj1, ['( delta > 10 )'] ) ;
    end

    %--- For the caption
    narasev = dbquery(dbj1, 'dbRECORD_COUNT') ;
    ev_nums = [ ev_type '_total_events' ] ;
    pfput( pfinfo, ev_nums, narasev ) ;


    %--- Generate rose plots
    for i=1:narasev,
        dbj1.record = i - 1 ;
        [delta,seaz] = dbgetv( dbj1, 'assoc.delta','assoc.seaz') ;
        if( strcmp( ev_type, 'regional' ) ) 
            my_local_sta2ev_dist(i) =  delta ;
            my_local_sta2ev_az(i) =  seaz * pi/180 ;
        else
            my_tele_sta2ev_dist(i) = delta ;
            my_tele_sta2ev_az(i) =  seaz * pi/180 ;
        end

    end

    if( strcmp( ev_type, 'regional' ) ) 

        eol_hist_local = figure('Visible','off') ;
        eol_hist_local_x1 = 0:1:dc;
        hist(my_local_sta2ev_dist,eol_hist_local_x1);
        title(['Event distribution by distance intervals from station:  ', mysta], 'FontSize', 14);
        set(gca,'XLim', [0 dc]);
        yrange1 = get(gca,'ylim');
        ymax1   = yrange1(:,2);
        set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
        set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
        set(eol_hist_local, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

        %--- Print to a file
        eol_hist_local_file = [ imgdir '/' mysta '_' ev_type '_hist.eps' ];
	print( '-depsc2',eol_hist_local_file ) ;
        % printstr = [ 'print -dpng -r72 ' eol_hist_local_file ];
        % eval( printstr ) ;

        eol_rose_local = figure('Visible','off') ;
        [tout, rout] = rose(my_local_sta2ev_az,36);
        polar(tout,rout);
        [xout, yout] = pol2cart(tout,rout);
        set(gca, 'nextplot', 'add');
        fill(xout, yout, 'r');
        set(gca,'View',[-90 90], 'Ydir','reverse');

        %--- Print to a file
        eol_rose_local_file = [ imgdir '/' mysta '_' ev_type '_rose.eps' ];
	print( '-depsc2',eol_rose_local_file ) ;
        % printstr = [ 'print -dpng -r72 ' eol_rose_local_file ];
        % eval( printstr ) ;

    else

        eol_hist_tele = figure('Visible','off') ;
        eol_hist_tele_x2 = dc:10:180;
        hist(my_tele_sta2ev_dist,eol_hist_tele_x2);
        title(['Event distribution by distance intervals from station:  ', mysta], 'FontSize', 14);
        yrange2 = get(gca,'ylim');
        ymax2   = yrange2(:,2);
        xlim([dc 180]);
        set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
        set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
        set(eol_hist_tele, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

        %--- Print to a file
        eol_hist_tele_file = [ imgdir '/' mysta '_' ev_type '_hist.eps' ];
	print( '-depsc2',eol_hist_tele_file ) ;
        % printstr = [ 'print -dpng -r72 ' eol_hist_tele_file ];
        % eval( printstr ) ;
      
        eol_rose_tele = figure('Visible','off') ;
        [tout, rout] = rose(my_tele_sta2ev_az,36);
        polar(tout,rout);
        [xout, yout] = pol2cart(tout,rout);
        set(gca, 'nextplot', 'add');
        fill(xout, yout, 'r');
        set(gca,'View',[-90 90], 'Ydir','reverse');

        %--- Print to a file
        eol_rose_tele_file = [ imgdir '/' mysta '_' ev_type '_rose.eps' ];
	print( '-depsc2',eol_rose_tele_file ) ;
        % printstr = [ 'print -dpng -r72 ' eol_rose_tele_file ];
        % eval( printstr ) ;

    end

    %--- Free up memory
    pffree( pfinfo ) ;
    dbclose( db ) ;

    clear all ;

end
