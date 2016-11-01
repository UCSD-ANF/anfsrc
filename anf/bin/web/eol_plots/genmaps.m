%-----------------------------------------------------
%  Plot maps for a particular station
%-----------------------------------------------------
%
% A Matlab script for plotting stations on global maps
% reyes@ucsd.edu
%
%-----------------------------------------------------

function genmaps( mysta, ev_type, event_list, sta_lat, sta_lon, imgdir )

    ImageDPI=200;
    set_fig( 1 )

    ev_mag = 0 ;
    ev_time = 0 ;
    ev_lat = sta_lat ;
    ev_lon = sta_lon ;

    dc = 10 ;


    % Find a big event to plot
    for i=1:length(event_list)
        if strcmp( ev_type, event_region(sta_lat, sta_lon, event_list( i ), dc) )
            if event_list( i ).mag > ev_mag
                ev_mag = event_list( i ).mag ;
                ev_lat = event_list( i ).Lat ;
                ev_lon = event_list( i ).Lon ;
                ev_time = event_list( i ).time ;
                ev_arrivaltime = event_list( i ).arrival ;
            end
        end
    end


    event_start = ev_arrivaltime + ( ( ev_arrivaltime - ev_time ) * 1 ) ;
    event_end   = ev_arrivaltime + ( ( ev_arrivaltime - ev_time ) * 3 ) ;

    if( strcmp( ev_type, 'regional' ) )
        axes('position',[ .05,.05,.9,.9 ] ) ;
        load topo;
        %event_start = ev_time - 10 ;
        %event_end = ev_time + 50 ;

        latlim = [ sta_lat-dc,  sta_lat+dc ];
        lonlim = [ sta_lon-dc,  sta_lon+dc ];

        % Make a regional map
        gtopo30s( latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/hf/save/maps/gtopo30/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('Matlab_code/eol_plots/global/', 5, latlim, lonlim ) ;
        %[ Z, refvec ] = gtopo30('/anf/ANZA/legacy_data/array/maps/gtopo30/', 5, latlim, lonlim ) ;
        [ Z, refvec ] = gtopo30('/Users/reyes/repos/anfsrc/anf/bin/web/eol_plots/tiles/', 17, latlim, lonlim ) ;
        zlen = length( Z ) ;
        worldmap( Z, refvec ) ;
        %--- Plot as an image - don't need a surface
        % geoshow( Z, refvec, 'DisplayType', 'surface' ) ;
        geoshow( Z, refvec, 'DisplayType', 'image' ) ;

        %--- Convert gtopo30 NaN's to zeroes
        notNaN = ~isnan(Z) ;
        howMany = sum( notNaN ) ;
        Z(~notNaN) = -200 ;

        %--- Apply the colormap
        colormap( demcmap(Z) ) ;
        hs = meshm(Z, refvec, size(Z));
    else
        %event_start = ev_time ;
        %event_end = ev_time + 300 ;

        axes('position',[ 0,0,1,1 ] ) ; 
        % Make a global map
        load topo;
        axesm( 'ortho', 'Origin', [ 15 sta_lon 0 ] ) ;
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


    figname = [ mysta '_' ev_type '_map' ] ;
    save_png( imgdir, figname, ImageDPI ) ;


    % Run function to make waveforms for this event
    waveformplots( ev_type, imgdir, mysta, 'BH.*', event_start, event_end )

end 
