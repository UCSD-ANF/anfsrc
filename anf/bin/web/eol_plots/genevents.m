%-----------------------------------------------------
%  Plot events for the lifetime of the station
%-----------------------------------------------------
%
% A Matlab script for plotting events
%
% @category  Datascope
% @package   Matlab
% @author    Rob Newman <rlnewman@ucsd.edu>
% @copyright Copyright (c) 2007 UCSD
% @license   MIT-style license
% @version   1.0
%
% v1.0.1 2008-01-24
%
%-----------------------------------------------------

function genevents( mysta, ev_type, ev_database, mysta_lat, mysta_lon, imgdir, eventinfopf ) 

    %--- TEST CASE
    % mysta = 'BNLO' ;
    % ev_type = 'large' ;
    % ev_type = 'regional' ;
    % ev_database = '/tmp/eol_events_BNLO/BNLO_comp' ;
    % mysta_lat = 37.1311 ;
    % mysta_lon = -122.1729 ;
    % imgdir = '/anf/anfops1/usarray/plots/eol_representative_event_plots' ;

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

    %--- Set up bkgrd and frgrd colors
    figure('Visible','off');

    whitebg( [ 1 1 1 ] ) ;
    set( gcf, 'Color', [ 1, 1, 1 ] ) ;
    set( gcf, 'PaperPositionMode', 'manual' ) ;
    set( gcf, 'PaperUnits', 'inches' ) ;
    set( gcf, 'PaperOrientation', 'portrait' ) ;
    %--- set( gcf, 'PaperSize', [ 7 5 ] ) ;
    %--- set( gcf, 'PaperType', 'B2' ) ;

    %--- Ensure enough room for map axes to be displayed
    if( strcmp( ev_type, 'regional' ) )
        axes('position',[ .05,.05,.9,.9 ] ) ; 
    else
        axes('position',[ 0,0,1,1 ] ) ; 
    end

    for i=1:narasev,

        dbj1.record = i - 1 ;
        [lat,lon,mb,ms,ml] = dbgetv( dbj1, 'lat', 'lon','mb','ms','ml' ) ;

        %--- ml is equivalent to Mw
        %--- mag is never empty, NULL values are -999
        if( strcmp( ev_type, 'regional' ) )
            if ml < 0
                if mb < 0
                    if ms > 0 
                        mag = ceil( ms ) ;
                    else
                        mag = 2 ; %--- Default size
                    end
                else
                    mag = ceil( mb ) ;
                end
            else
                mag = ceil( ml ) ;
            end
        else
            if ml < 0
                if mb < 0
                    if ms > 0 
                        mag = ceil( ms ) ;
                    else
                        mag = 2 ; %--- Default size
                    end
                else
                    mag = ceil( mb ) ;
                end
            else
                mag = ceil( ml ) ;
            end
        end 

        [ point(i).Geometry ] = deal('Point') ;
        [ point(i).Lat ] = deal( lat ) ;
        [ point(i).Lon ] = deal( lon ) ;
        [ point(i).Cluster ] = deal( mag ) ;

    end

    clear mag ;

    sta_no = narasev + 1 ;
    [ point( sta_no ).Geometry ] = deal('Point') ;
    [ point( sta_no ).Lat ] = deal( mysta_lat ) ;
    [ point( sta_no ).Lon ] = deal( mysta_lon ) ;
    [ point( sta_no ).Cluster ] = deal( 20 ) ;

    %--- Define the symbol styles
    symbols = makesymbolspec( 'Point',...
        { 'Cluster', 1, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 2 },...
        { 'Cluster', 2, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 4 },...
        { 'Cluster', 3, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 8 },...
        { 'Cluster', 4, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 12 },...
        { 'Cluster', 5, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 16 },...
        { 'Cluster', 6, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 20 },...
        { 'Cluster', 7, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 24 },...
        { 'Cluster', 8, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 28 },...
        { 'Cluster', 9, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 32 },...
        { 'Cluster', 10, 'Color',[ 0 0 0 ], 'Marker', 's', 'MarkerFaceColor', [ 1 .6 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 36 },...
        { 'Cluster', 20, 'Color',[ 0 0 0 ], 'Marker', '^', 'MarkerFaceColor', [ 1 0 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 10 }...
    ) ;

    if( strcmp( ev_type, 'regional' ) )
        load topo;
        latlim = [ lat_min lat_max ] ;
        lonlim = [ lon_min lon_max ] ;

        % Make a regional map
        gtopo30s( latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/hf/save/maps/gtopo30/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('Matlab_code/eol_plots/global/', 5, latlim, lonlim ) ;
        [ Z, refvec ] = gtopo30('/anf/ANZA/legacy_data/array/maps/gtopo30/', 5, latlim, lonlim ) ;
        zlen = length( Z ) ;
        worldmap( Z, refvec ) ;
        geoshow( Z, refvec, 'DisplayType', 'image' ) ;
        % axesm( 'eqacylin', 'Origin', [ proj_lat proj_lon 0 ] ) ;

        %--- Convert gtopo30 NaN's to zeroes
        notNaN = ~isnan(Z) ;
        howMany = sum( notNaN ) ;
        Z(~notNaN) = -200 ;

        %--- Apply the colormap
        colormap( demcmap(Z) ) ;
        hs = meshm(Z, refvec, size(Z));
    else
        % Make a global map
        load topo;
        % Make the edge white
        axesm( 'eqdazim', 'Origin', [ 15 mysta_lon 0 ], 'Frame', 'on', 'FEdgeColor', [ 0 0 0 ] ) ;
        demcmap(topo);
        hs = meshm(topo, topolegend, size(topo));
        set( gca, 'Visible', 'off' ) ;
    end

    S = shaperead('landareas', 'UseGeoCoords', true) ;
    geoshow( point, 'SymbolSpec', symbols ) ;

    %--- Title
    %--- NOT REQUIRED ANY MORE
%
%    if( strcmp( ev_type, 'regional' ) )

        %--- mytitle = { 
        %---     [ 'Plot of all regional events (within ' sprintf( '%0.5g', range*2 ) ' deg.) detected by station ' mysta ' over deployment' ] ;...
        %---     [ 'lifetime. The red triangle is the station location, orange squares are earthquake ' ] ;...
        %---     [ 'epicenters, sized by magnitude. A larger size represents a larger event.' ] ;...
        %---     [ 'Total number of events plotted is ' int2str( narasev ) '.' ] ...
        %--- } ; 
%        mytitle = { 
%            [ 'Regional events detected by station TA_' mysta '. The size of the orange squares is proportional to the magnitude of the event. Station TA_' mysta ' is shown by the red triangle.' ] ...
%        } ; 
%        mypftitle = 'regional_total_events' ;
%        pfput( pfinfo, mypftitle, mytitle ) ;
%    else 
        %--- mytitle = { 
        %---    [ 'Equidistant azimuthal projection plot of Mw 6.5 and larger teleseismic events detected' ] ;...
        %---    [ 'by station ' mysta ' over deployment lifetime. The red triangle is the station location,' ] ;...
        %---    [ 'orange squares are earthquake epicenters, sized by magnitude. A larger size' ] ;...
        %---    [ 'represents a larger event. Total number of events plotted is ' int2str( narasev ) '.' ] ...
        %--- } ; 
%        mytitle = { 
%            [ 'The map above shows the location of ' int2str( narasev ) ' distant events (greater than 10 degrees from the station) detected by station TA_' mysta '. The size of the orange squares is proportional to the magnitude of the event. Station TA_' mysta ' is shown as a red triangle.' ] ...
%        } ; 
%        mypftitle = 'large_total_caption' ;
%        pfput( pfinfo, mypftitle, mytitle ) ;
%    end 

%    pfput( pfinfo, mypftitle, mytitle ) ;

    %--- Write the parameter file object out
    pfwrite( pfinfo, eventinfopf ) ;

    %--- axes('position',[0,0,1,.9] ) ; 
    %--- htext = text( .5, 0.1, mytitle, 'FontSize',14 ) ; 
    %--- set( htext, 'HorizontalAlignment','center' ) ; 
    %--- set( gca, 'Visible','off' ) ;


    %--- Free up memory
    pffree( pfinfo ) ;
    dbclose( db ) ;

    %--- Print to a file
    %--- set(gcf, 'inverthardcopy', 'off');
    figname = [ imgdir mysta '_' ev_type '_lifetime_distribution.eps' ] ;
    print( '-depsc2',figname ) ;
    % printstr = [ 'print -dpng -r72 ' figname ];
    % eval( printstr ) ;

    clear all ;

end
