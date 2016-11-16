%-----------------------------------------------------
%  Save plot to disk and convert to PNG
%-----------------------------------------------------
%
% A Matlab script saving figures to disk as PS files
% and converting them to PNG format.
% reyes@ucsd.edu
%
%-----------------------------------------------------

function file = save_png( filename, dpi )

    global CONVERT ;
    global station ;
    global imgdir ;

    stadir = fullfile( imgdir, station ) ;
    if ~exist(stadir, 'dir')
        mkdir( stadir ) ;
    end

    eps = [ imgdir '/' station '/' filename '.eps' ] ;
    png = [ imgdir '/' station '/' filename '.png' ] ;

    % Remove previous image file
    if exist(eps, 'file')==2
        delete(eps);
    end

    % Save image to disk
    print( '-depsc2', eps , strcat('-r',num2str(dpi))) ;


    % Try to convert to new format
    if exist( eps, 'file' )==2
        fprintf( '%s successfully created. Now convert and trim it.\n', eps ) ;
        %system( sprintf( '/opt/local/bin/convert %s %s', eps, png) );
        %system( sprintf( '/usr/bin/convert %s %s', eps, png) );
        system( sprintf( '%s %s %s', CONVERT, eps, png) );

        if exist(png, 'file')==2
            delete(eps);
            file = png ;
        else
            fprintf( '%s image not created!\n', png ) ;
            file = eps ;
        end

    else
        fprintf( '%s image not created!\n', eps ) ;
        file = '' ;
    end

end
