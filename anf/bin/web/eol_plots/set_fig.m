%-----------------------------------------------------
%  Configure Matlab figure
%-----------------------------------------------------
%
% A Matlab script to configure the FIGURE that we
% need for our data.
% reyes@ucsd.edu
%
%-----------------------------------------------------

function set_fig( multiplier )

    figure('Visible','off');

    units='inches';
    if multiplier
        larger = multiplier ;
    else
        larger = 1 ;

    whitebg( [ 1 1 1 ] ) ;
    set( gcf, 'Color', [ 1, 1, 1 ] ) ;

    set(gcf,'PaperPositionMode','manual')
    set(gcf,'Units',units );
    set(gcf,'PaperUnits',units );
    resize = get(gcf,'Position');
    resize = resize * larger;
    set(gcf,'Position',[0 0 resize(3) resize(4)])
    set(gcf,'PaperPosition',[0 0 resize(3) resize(4)])
    set(gcf,'PaperSize', [resize(3) resize(4)] );

end
