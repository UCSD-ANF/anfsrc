%-----------------------------------------------------
%  Plot roseplot of events for lifetime of the station
%-----------------------------------------------------
%
% A Matlab script for plotting events in polar plots
% reyes@ucsd.edu
%
%-----------------------------------------------------

function roseplots( event_list )

    global station ;
    global latitude ;
    global longitude ;

    ImageDPI = 200 ;
    set_fig( 1 )
    success = 0 ;

    %--- What defines the spacing in the graphs
    dc = 10 ;


    for i=1:length(event_list)
        if strcmp( 'regional', event_region(latitude, longitude, event_list( i ), dc) )
            my_local_sta2ev_dist(i) =  event_list(i).delta ;
            my_local_sta2ev_az(i) =  event_list(i).seaz * pi/180 ;
            success = 1 ;
        else
            my_tele_sta2ev_dist(i) = event_list(i).delta ;
            my_tele_sta2ev_az(i) =  event_list(i).seaz * pi/180 ;
            success = 1 ;
        end
    end

    if success < 1
        x = length(event_list) ;
        my_local_sta2ev_dist(x) =  event_list(x).delta ;
        my_local_sta2ev_az(x) =  event_list(x).seaz * pi/180 ;
        my_tele_sta2ev_dist(x) = event_list(x).delta ;
        my_tele_sta2ev_az(x) =  event_list(x).seaz * pi/180 ;
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
    title(['Event distribution by distance intervals from station:  ', station], 'FontSize', 14);
    set(gca,'XLim', [0 dc]);
    yrange1 = get(gca,'ylim');
    ymax1   = yrange1(:,2);
    set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
    set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
    set(eol_hist_local, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

    %--- Print to a file
    figname = [ station '_regional_hist' ] ;
    save_png( figname, ImageDPI ) ;


    %
    % regional events rose
    %
    eol_rose_local = figure('Visible','off') ;
    try
        [tout, rout] = rose(my_local_sta2ev_az,36);
        polar(tout,rout);
        [xout, yout] = pol2cart(tout,rout);
        set(gca, 'nextplot', 'add');
        fill(xout, yout, 'r');
        set(gca,'View',[-90 90], 'Ydir','reverse');
    catch exception
        disp(exception.identifier) ;
    end

    %--- Print to a file
    figname = [ station '_regional_rose' ] ;
    save_png( figname, ImageDPI ) ;



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

    title(['Event distribution by distance intervals from station:  ', station], 'FontSize', 14);
    yrange2 = get(gca,'ylim');
    ymax2   = yrange2(:,2);
    xlim([dc 180]);
    set(get(gca,'YLabel'), 'String','# of events', 'FontSize', 14);
    set(get(gca,'XLabel'), 'String','Distance (delta) in degrees', 'FontSize', 14);
    set(eol_hist_tele, 'units', 'normalized', 'position', [0.13 0.11 0.775 0.815]);

    %--- Print to a file
    figname = [ station '_large_hist' ] ;
    save_png( figname, ImageDPI ) ;



    %
    % global events rose
    %
    eol_rose_tele = figure('Visible','off') ;
    try
        [tout, rout] = rose(my_tele_sta2ev_az,36);
        polar(tout,rout);
        [xout, yout] = pol2cart(tout,rout);
        set(gca, 'nextplot', 'add');
        fill(xout, yout, 'r');
        set(gca,'View',[-90 90], 'Ydir','reverse');
    catch exception
        disp(exception.identifier) ;
    end

    %--- Print to a file
    figname = [ station '_large_rose' ] ;
    save_png( figname, ImageDPI ) ;


end
