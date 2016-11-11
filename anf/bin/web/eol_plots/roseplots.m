%-----------------------------------------------------
%  Plot roseplot of events for lifetime of the station
%-----------------------------------------------------
%
% A Matlab script for plotting events in polar plots
% reyes@ucsd.edu
%
%-----------------------------------------------------

function roseplots( mysta, event_list, sta_lat, sta_lon, imgdir )


    ImageDPI = 200 ;
    set_fig( 1 )

    %--- What defines the spacing in the graphs
    dc = 10 ;


    for i=1:length(event_list)
        if strcmp( 'regional', event_region(sta_lat, sta_lon, event_list( i ), dc) )
            my_local_sta2ev_dist(i) =  event_list(i).delta ;
            my_local_sta2ev_az(i) =  event_list(i).seaz * pi/180 ;
        else
            my_tele_sta2ev_dist(i) = event_list(i).delta ;
            my_tele_sta2ev_az(i) =  event_list(i).seaz * pi/180 ;
        end
    end


    %
    % regional events histogram
    %

    eol_hist_local = figure('Visible','off') ;
    eol_hist_local_x1 = 0:1:dc;
    try
        hist(my_local_sta2ev_dist,eol_hist_local_x1);
    catch exception
        disp(exception.identifier) ;
    end
    title(['Event distribution by distance intervals from station:  ', mysta], 'FontSize', 14);
    set(gca,'XLim', [0 dc]);
    yrange1 = get(gca,'ylim');
    ymax1   = yrange1(:,2);
    set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
    set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
    set(eol_hist_local, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

    %--- Print to a file
    figname = [ mysta '_regional_hist' ] ;
    save_png( imgdir, mysta, figname, ImageDPI ) ;


    %
    % regional events rose
    %
    eol_rose_local = figure('Visible','off') ;
    try
        [tout, rout] = rose(my_local_sta2ev_az,36);
        polar(tout,rout);
    catch exception
        disp(exception.identifier) ;
    end
    [xout, yout] = pol2cart(tout,rout);
    set(gca, 'nextplot', 'add');
    fill(xout, yout, 'r');
    set(gca,'View',[-90 90], 'Ydir','reverse');

    %--- Print to a file
    figname = [ mysta '_regional_rose' ] ;
    save_png( imgdir, figname, ImageDPI ) ;



    %
    % global events histogram
    %
    eol_hist_tele = figure('Visible','off') ;
    eol_hist_tele_x2 = dc:10:180;

    try
        hist(my_tele_sta2ev_dist,eol_hist_tele_x2);
    catch exception
        disp(exception.identifier) ;
    end

    title(['Event distribution by distance intervals from station:  ', mysta], 'FontSize', 14);
    yrange2 = get(gca,'ylim');
    ymax2   = yrange2(:,2);
    xlim([dc 180]);
    set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
    set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
    set(eol_hist_tele, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

    %--- Print to a file
    figname = [ mysta '_large_hist' ] ;
    save_png( imgdir, figname, ImageDPI ) ;



    %
    % global events rose
    %
    eol_rose_tele = figure('Visible','off') ;
    try
        [tout, rout] = rose(my_tele_sta2ev_az,36);
        polar(tout,rout);
    catch exception
        disp(exception.identifier) ;
    end
    [xout, yout] = pol2cart(tout,rout);
    set(gca, 'nextplot', 'add');
    fill(xout, yout, 'r');
    set(gca,'View',[-90 90], 'Ydir','reverse');

    %--- Print to a file
    figname = [ mysta '_large_rose' ] ;
    save_png( imgdir, figname, ImageDPI ) ;


end
