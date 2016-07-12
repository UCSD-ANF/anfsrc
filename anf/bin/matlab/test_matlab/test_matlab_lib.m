% Simple code to test Matlab
% Juan Reyes
% reyes@ucsd.edu


% Example of interpolation and data 
% gridding functions that operate 
% specifically on multidimensional 
% data. This is an example of NDGRID
% applied to an N-dimensional matrix.


% Configure Antelope - Matlab
currentFolder = pwd

cd([getenv('ANTELOPE') '/data/matlab/R2015a/antelope/scripts/']);
setup_antelope; 

cd currentFolder;


% Verify if we are set to run in verbose. We
% do this by passing a "run_verbose" variable
% from controller. 
verbose = 0;
if exist('run_verbose')
    if strcmpi(eval('run_verbose') , 'True')
        verbose = 1;
    end
end


% Verify if we have a parameter file to load. 
if exist('pf')
    pf_file = eval('pf');
else
    pf_file = 'demo_pf_file.pf';
end

if verbose
    fprintf('pf_file=> %s\n', pf_file);
end




x1 = -2*pi:pi/10:0;
x2 = 2*pi:pi/10:4*pi;
x3 = 0:pi/10:2*pi;
[x1,x2,x3] = ndgrid(x1,x2,x3);

z = x1 + exp(cos(2*x2.^2)) + sin(x3.^3);
slice(z,[5 10 15], 10, [5 12]);

if verbose
    fprintf('size(Z)=> ')
    disp(size( z ));
end 


psfile = 'test.eps';
ImageDPI=700;
units='inches';
multiplier = 4;

% More info http://www.mathworks.com/help/matlab/ref/figure-properties.html
fig = gcf;

set(gcf,'PaperPositionMode','manual')
set(fig,'Units',units );
set(fig,'PaperUnits',units );
resize = get(fig,'Position');
resize = resize * multiplier;
set(fig,'Position',[0 0 resize(3) resize(4)])
set(fig,'PaperPosition',[0 0 resize(3) resize(4)])
set(fig,'PaperSize', [resize(3) resize(4)] );


% Remove previous image file
if exist(psfile, 'file')==2
      delete(psfile);
end

print( '-depsc2', psfile , strcat('-r',num2str(ImageDPI))) ;
