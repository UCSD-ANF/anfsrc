%-----------------------------------------------------
%  Plot events for the lifetime of the station
%-----------------------------------------------------
%
% A Matlab script for plotting events on global maps
% reyes@ucsd.edu
%
%-----------------------------------------------------

function genevents( mysta, ev_type, event_list, mysta_lat, mysta_lon, imgdir )

    %--- Set up bkgrd and frgrd colors
    % More info http://www.mathworks.com/help/matlab/ref/figure-properties.html

    ImageDPI=200;
    set_fig( 1 ) ;


    %--- Ensure enough room for map axes to be displayed
    if( strcmp( ev_type, 'regional' ) )
        axes('position',[ .05,.05,.9,.9 ] ) ;
    else
        axes('position',[ 0,0,1,1 ] ) ;
    end


    sta_no = length(event_list)+ 1 ;
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
        range = 10 ;
        lat_min = mysta_lat - range ;
        lat_max = mysta_lat + range ;
        lon_min = mysta_lon - range ;
        lon_max = mysta_lon + range ;
        latlim = [ lat_min lat_max ] ;
        lonlim = [ lon_min lon_max ] ;

        % Make a regional map
        % gtopo30s( latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/hf/save/maps/gtopo30/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('Matlab_code/eol_plots/global/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/anf/ANZA/legacy_data/array/maps/gtopo30/', 5, latlim, lonlim )

        [ Z, refvec ] = gtopo30('/Users/reyes/repos/anfsrc/anf/bin/web/eol_plots/tiles/', 17, latlim, lonlim ) ;
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

    geoshow( event_list, 'SymbolSpec', symbols ) ;

    figname = [ mysta '_' ev_type '_lifetime_distribution' ] ;
    save_png( imgdir, figname, ImageDPI ) ;


end
