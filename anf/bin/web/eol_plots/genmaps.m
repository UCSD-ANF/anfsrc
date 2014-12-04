%%
function genmaps( mysta, ev_time, ev_mag, ev_type, sta_lat, sta_lon, ev_lat, ev_lon, imgdir, eventinfopf ) 

    %--- Uncomment for testing
    % m = 1 ;
    % mysta = 'BNLO' ;
    % readabletime = 'October 27, 2007 10:00' ;
    % ev_type = 'regional' ;
    % ev_type = 'large' ;
    % ev_mag = '5.7Mw' ;
    % sta_lat = 45 ;
    % sta_lon = -120.44 ;
    % ev_lat = 50 ;
    % ev_lon = -140 ;
    % imgdir = '/anf/anfops1/usarray/plots/eol_representative_event_plots' ;

    %--- For double checking inputs are good
    % sta_lat
    % sta_lon
    % ev_lat
    % ev_lon

    if exist( eventinfopf ) == 0 
        pfinfo = dbpf() ;
    else 
        pfinfo = dbpf( eventinfopf ) ;
    end

    %--- Determine projection origin for longitude
    if( strcmp( ev_type, 'regional' ) )
         %--- Get lat range
         if sta_lat > ev_lat 
             proj_lat = ( ( sta_lat - ev_lat ) / 2 ) + ev_lat ;
             lat_lim_min = ev_lat - 5 ;
             lat_lim_max = sta_lat + 5 ;
         else 
             proj_lat = ( ( ev_lat - sta_lat ) / 2 ) + sta_lat ;
             lat_lim_min = sta_lat - 5 ;
             lat_lim_max = ev_lat + 5 ;
         end

         %--- Get lon range
         if sta_lon > ev_lon 
             proj_lon = ( ( sta_lon - ev_lon ) / 2 ) + ev_lon ;
             lon_lim_min = ev_lon - 5 ;
             lon_lim_max = sta_lon + 5 ;
         else 
             proj_lon = ( ( ev_lon - sta_lon ) / 2 ) + sta_lon ;
             lon_lim_min = sta_lon - 5 ;
             lon_lim_max = ev_lon + 5 ;
         end
    end


    if sta_lon < 0 && ev_lon > 0
        standard_sta_lon = 360 + sta_lon ;
        standard_ev_lon = ev_lon ;
    elseif sta_lon > 0 && ev_lon > 0
        standard_sta_lon = sta_lon ;
        standard_ev_lon = ev_lon ;
    else
        standard_sta_lon = 360 + sta_lon ;
        standard_ev_lon = 360 + ev_lon ;
    end

    if standard_ev_lon > standard_sta_lon
        proj_lon = ( standard_sta_lon - standard_ev_lon ) / 2 + standard_ev_lon ;
    else
        proj_lon = ( standard_ev_lon - standard_sta_lon ) / 2 + standard_sta_lon ;
    end

    figure('Visible','off') ;

    whitebg( [ 1 1 1 ] ) ;
    set( gcf, 'Color', [ 1, 1, 1 ] ) ;
    set( gcf, 'PaperPositionMode', 'manual' ) ;
    set( gcf, 'PaperUnits', 'inches' ) ;
    set( gcf, 'PaperOrientation', 'portrait' ) ;
    %--- set( gcf, 'PaperPosition', [0 0 3.3 3.3] ) ;

    %%%% set( gcf, 'PaperSize', [ 7 5 ] ) ;
    %%%% set( gcf, 'PaperType', 'B2' ) ;

    %--- Ensure enough room for title
    %%%% axes('position',[0,.175,1,.8] ) ; 

    %--- No title - go right to edge and use full page

    if( strcmp( ev_type, 'regional' ) )
        axes('position',[ .05,.05,.9,.9 ] ) ; 
        load topo;
        latlim = [ lat_lim_min lat_lim_max ];
        lonlim = [ lon_lim_min lon_lim_max ];

        % Make a regional map
        gtopo30s( latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/hf/save/maps/gtopo30/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('bin/eol_plots/global/', 5, latlim, lonlim ) ;
        [ Z, refvec ] = gtopo30('/anf/ANZA/legacy_data/array/maps/gtopo30/', 5, latlim, lonlim ) ;
        zlen = length( Z ) ;
        worldmap( Z, refvec ) ;
        %--- Plot as an image - don't need a surface
        % geoshow( Z, refvec, 'DisplayType', 'surface' ) ;
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
        axes('position',[ 0,0,1,1 ] ) ; 
        % Make a global map
        load topo;
        axesm( 'ortho', 'Origin', [ 15 proj_lon 0 ] ) ;
        demcmap(topo);
        hs = meshm(topo, topolegend, size(topo));
        set( gca, 'Visible', 'off' ) ;
    end

    [ point(1).Geometry ] = deal('Point') ;
    [ point(1).Lat ] = deal( sta_lat ) ;
    [ point(1).Lon ] = deal( sta_lon ) ;
    [ point(1).Cluster ] = deal( 1 ) ;
    [ point(1).z ] = deal( 10000 ) ;

    [ point(2).Geometry ] = deal('Point') ;
    [ point(2).Lat ] = deal( ev_lat ) ;
    [ point(2).Lon ] = deal( ev_lon ) ;
    [ point(2).Cluster ] = deal( 2 ) ;
    [ point(2).z ] = deal( 10000 ) ;

    %--- Define the symbol styles
    symbols = makesymbolspec( 'Point',...
        { 'Cluster', 1, 'Visible', 'on', 'Color',[ 0 0 0 ], 'Marker', '^', 'MarkerFaceColor', [ 1 0 0 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 20 },...
        { 'Cluster', 2, 'Visible', 'on', 'Color',[ 0 0 0 ], 'Marker', 'p', 'MarkerFaceColor', [ 1 1 1 ], 'MarkerEdgeColor', [ 0 0 0 ], 'MarkerSize', 30 }...
    ) ;

    S = shaperead('landareas', 'UseGeoCoords', true) ;

    geoshow( point, 'SymbolSpec', symbols ) ;

    %--- Title
    %--- NOT REQUIRED ANYMORE
%    mytitle = { 
%        [ 'The location of station TA_' mysta ' is shown by the red triangle; the white star depicts the location on the surface directly above the earthquake.' ] ...
%    } ; 

%    if( strcmp( ev_type, 'regional' ) )
%        mypftitle = 'regional_wform_event_map_caption' ;
%    else 
%        mypftitle = 'large_wform_event_map_caption' ;
%    end 

%    pfput( pfinfo, mypftitle, mytitle ) ;

    %--- Write the parameter file object out
%    pfwrite( pfinfo, eventinfopf ) ;

    %--- Free up memory
    pffree( pfinfo ) ;

%%%%    mytitle = { 
%%%%       [ 'Map from ' ev_type ' event detected by station ' mysta ' on ' ] ;...
%%%%       [ ev_time ' UTC. The magnitude of this event was ' ev_mag '. ' ] ;...
%%%%       [ 'The white star is the event epicenter and the red triangle is the station location.' ] ...
%%%%    } ; 
%%%%    axes('position',[0,0,1,.9] ) ; 
%%%%    htext = text( .5, 0.1, mytitle, 'FontSize',14 ) ; 
%%%%    set( htext, 'HorizontalAlignment','center' ) ; 
%%%%    set( gca, 'Visible','off' ) ;


    %--- Print to a file
    %--- set(gcf, 'inverthardcopy', 'off');
    figname = [ imgdir mysta '_' ev_type '_map.eps' ] ;
    print( '-depsc2',figname ) ;
    % printstr = [ 'print -dpng -r72 ' figname ];
    % eval( printstr ) ;

end 
