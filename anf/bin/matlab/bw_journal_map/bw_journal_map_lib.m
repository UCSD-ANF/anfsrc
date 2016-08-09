%  This code opens the full-met station list from the DB and the list of NWS stations from an Excel spreadsheet and plots them together on a map for figures.

clc;
clear all;

% pf = 'map_for_journals_alaska_greyscale.pf';

% dbpf(pf)
% pf = dbpf('TAParameterfile.pf');
% 
% pfkeys(pf);
% 
% TA_Values = pfget_string(pf,'TA_Parameter');









pf = dbpf('map_for_journals_alaska_greyscale.pf');



pfkeys(pf);

lonlim_array = pfget_tbl(pf,'lonlim');
lonlim=[lonlim_array{1},lonlim_array{2}];

latlim_array = pfget_tbl(pf,'latlim');
latlim=[latlim_array{1},latlim_array{2}];

name_of_excel = pfget_string(pf,'name_of_excel');
name_of_excel_0 = pfget_string(pf,'name_of_excel_0');
name_of_excel_2 = pfget_string(pf,'name_of_excel_2');
name_of_excel_3 = pfget_string(pf,'name_of_excel_3');
excel_file_2 = pfget_string(pf,'excel_file_2');
shape_file = pfget_string(pf,'shape_file');


alaska_cities = pfget_string(pf,'alaska_cities');




%%% SECTION 1 - OPEN THE NWS STATION DATA AND LOAD THE STATIONS AS PROPER LAT/LON COORDINATES

% Open Excel spreadsheet

%Open the excel file that contains the data for placeholder Alaskan Cities 

[num11,txt11,raw11] = xlsread(alaska_cities);

[G11 H11] = size(raw11);



fprintf(['Read excel file' name_of_excel  ' along wiht others like it containing latitudes and longitudes of stations \n'])
% [num,txt,raw] = xlsread(name_of_excel);
% 
% fprintf('Assign variable G to number of stations in excel file \n')
% 
% [G H] = size(raw); % we want G, which includes the header row

[num1,txt1,raw1] = xlsread(name_of_excel_0);

[G1 H1] = size(raw1);

G1

[num6,txt6,raw2] = xlsread(name_of_excel_2);

[G2 H2] = size(raw2);

[num3,txt3,raw3] = xlsread(name_of_excel_3);

[G3 H3] = size(raw3);



G4 =  G1 + G2 + G3;

OutputCities = []; %output for the cities lat/lon array 
Output = []; % output for building lat/lon array for NWS stations
OutputG1 = [];
OutputG2 = [];
OutputG3 =[];



fprintf('Assign variables lat_NWS and lon_NWS to latitude and longitude of stations as well as other components \n')

for i = 1:G1  % this for-loop section loads the individual deg/min/sec columns for each row of each lat/lon value from the NWS station spreadsheet and converts them to their decimal coordinates
    
    lat_NWS = cell2mat(raw1(i,9)); 
    lat_min_NWS = cell2mat(raw1(i,10));
    lat_sec_NWS = cell2mat(raw1(i,11));
    is_abs_lat = lat_NWS/abs(lat_NWS); % will be 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.
    lon_NWS = cell2mat(raw1(i,12));
    lon_min_NWS = cell2mat(raw1(i,13));
    lon_sec_NWS = cell2mat(raw1(i,14));
    is_abs_lon = lon_NWS/abs(lon_NWS); % will bels(fullfile(matlabroot, 'toolbox', 'map', 'mapdata')) 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.

    latitude_NWS = (((abs(lat_sec_NWS)/60)+abs(lat_min_NWS))/60+abs(lat_NWS))*is_abs_lat; % this is where the individual columns are added together.  they need to be absolute values or we get the wrong results.  then, the final station coord is multiplied by the 1 or -1 placeholder as determined above.
    longitude_NWS = (((abs(lon_sec_NWS)/60)+abs(lon_min_NWS))/60+abs(lon_NWS))*is_abs_lon;
    altitude_NWS = 10000; % some nice big number so annotations don't get gobbled up by mountain ranges and such
    OutputG1 = [OutputG1;[latitude_NWS longitude_NWS altitude_NWS]]; % bulid the array of lat/lon decimal coords from the NWS stations
    
end

NWS_lat_OutputG1 = OutputG1(:,1); % define the NWS lat column
NWS_lon_OutputG1 = OutputG1(:,2); % define the NWS lon column
altitude_NWS_above_mapG1 = OutputG1(:,3); % define the altitude above the topographic map to plot annotations

for i = 1:G2  % this for-loop section loads the individual deg/min/sec columns for each row of each lat/lon value from the NWS station spreadsheet and converts them to their decimal coordinates
    
    lat_NWS = cell2mat(raw2(i,9)); 
    lat_min_NWS = cell2mat(raw2(i,10));
    lat_sec_NWS = cell2mat(raw2(i,11));
    is_abs_lat = lat_NWS/abs(lat_NWS); % will be 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.
    lon_NWS = cell2mat(raw2(i,12));
    lon_min_NWS = cell2mat(raw2(i,13));
    lon_sec_NWS = cell2mat(raw2(i,14));
    is_abs_lon = lon_NWS/abs(lon_NWS); % will bels(fullfile(matlabroot, 'toolbox', 'map', 'mapdata')) 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.

    latitude_NWS = (((abs(lat_sec_NWS)/60)+abs(lat_min_NWS))/60+abs(lat_NWS))*is_abs_lat; % this is where the individual columns are added together.  they need to be absolute values or we get the wrong results.  then, the final station coord is multiplied by the 1 or -1 placeholder as determined above.
    longitude_NWS = (((abs(lon_sec_NWS)/60)+abs(lon_min_NWS))/60+abs(lon_NWS))*is_abs_lon;
    altitude_NWS = 10000; % some nice big number so annotations don't get gobbled up by mountain ranges and such
    OutputG2 = [OutputG2;[latitude_NWS longitude_NWS altitude_NWS]]; % bulid the array of lat/lon decimal coords from the NWS stations
    
end
G2
NWS_lat_OutputG2 = OutputG2(:,1); % define the NWS lat column
NWS_lon_OutputG2 = OutputG2(:,2); % define the NWS lon column
altitude_NWS_above_mapG2 = OutputG2(:,3); % define the altitude above the topographic map to plot annotations


for i = 1:G3  % this for-loop section loads the individual deg/min/sec columns for each row of each lat/lon value from the NWS station spreadsheet and converts them to their decimal coordinates
    
    lat_NWS = cell2mat(raw3(i,9)); 
    lat_min_NWS = cell2mat(raw3(i,10));
    lat_sec_NWS = cell2mat(raw3(i,11));
    is_abs_lat = lat_NWS/abs(lat_NWS); % will be 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.
    lon_NWS = cell2mat(raw3(i,12));
    lon_min_NWS = cell2mat(raw3(i,13));
    lon_sec_NWS = cell2mat(raw3(i,14));
    is_abs_lon = lon_NWS/abs(lon_NWS); % will bels(fullfile(matlabroot, 'toolbox', 'map', 'mapdata')) 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.

    latitude_NWS = (((abs(lat_sec_NWS)/60)+abs(lat_min_NWS))/60+abs(lat_NWS))*is_abs_lat; % this is where the individual columns are added together.  they need to be absolute values or we get the wrong results.  then, the final station coord is multiplied by the 1 or -1 placeholder as determined above.
    longitude_NWS = (((abs(lon_sec_NWS)/60)+abs(lon_min_NWS))/60+abs(lon_NWS))*is_abs_lon;
    altitude_NWS = 10000; % some nice big number so annotations don't get gobbled up by mountain ranges and such
    OutputG3 = [OutputG3;[latitude_NWS longitude_NWS altitude_NWS]]; % bulid the array of lat/lon decimal coords from the NWS stations
    
end

NWS_lat_OutputG3 = OutputG3(:,1); % define the NWS lat column
NWS_lon_OutputG3 = OutputG3(:,2); % define the NWS lon column
altitude_NWS_above_mapG3 = OutputG3(:,3); % define the altitude above the topographic map to plot annotations

for i = 1:G11  
    lat_NWS = cell2mat(raw11(i,2)); 
%     lat_min_NWS = cell2mat(raw11(i,10));
%     lat_sec_NWS = cell2mat(raw11(i,11));
%     is_abs_lat = lat_NWS/abs(lat_NWS); % will be 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.
    lon_NWS = cell2mat(raw11(i,3));
%     lon_min_NWS = cell2mat(raw11(i,13));
%     lon_sec_NWS = cell2mat(raw11(i,14));
    is_abs_lon = lon_NWS/abs(lon_NWS); % will bels(fullfile(matlabroot, 'toolbox', 'map', 'mapdata')) 1 or -1, need to do this because the individual columns are added together.  The final decimal coord will be multiplied by 1 or -1 as needed.

    latitude_NWS_Cit = abs(lat_NWS); % this is where the individual columns are added together.  they need to be absolute values or we get the wrong results.  then, the final station coord is multiplied by the 1 or -1 placeholder as determined above.
    longitude_NWS_Cit = abs(lon_NWS);
    altitude_NWS_Cit = 10000; % some nice big number so annotations don't get gobbled up by mountain ranges and such
    OutputCities = [OutputCities;[latitude_NWS_Cit longitude_NWS_Cit altitude_NWS_Cit]]; % bulid the array of lat/lon decimal coords from the NWS stations
    
end

NWS_lat_Output_Cities = OutputCities(:,1);
NWS_lon_Output_Cities = -1*OutputCities(:,2);
NWS_alt_Output_Cities = OutputCities(:,3);
%%% SECTION 2 - OPEN THE ALASKA EXCEL SPREADSHEET AND LOAD THE STATION CORDINATES FOR THE CURRENT AND POTENTIAL STATIONS


%%fprintf(['Read excel file' excel_file_2 ' containing information on potential stations \n'])

 %%[num2,txt2,raw2] = xlsread(excel_file_2);

fprintf('Counts number of possible new stations and assigns to variable I \n')

%%[I J] = size(raw2); % we want I, which includes the header row
%%I

fprintf('Set up the array Output2 in which latitude and longitude values are stored  \n')

Output2 = []; % output for building lat/lon array for potential USArray Alaska stations

%%fprintf(['Run loop through'    excel_file_2     ', and extract latitude and longitude of potential stations\n'])
%%fprintf('Assign latidue and longitude to variables latitude_TA and longitude_TA \n')

db = dbopen(TA_Values,'r'); % location of realtime USArray TA data
db = dblookup_table(db,'site'); % grab the site table
db_unique_1 = dbsort(db,'dbSORT_UNIQUE','sta'); % uniquely sort the site table since some stations have several duplicate rows
db_unique_2 = dbsubset(db_unique_1,'lat>="50" && lat<"75" && lon>="-180" && lon<"-120"');
[sta,lat_TA,lon_TA]=dbgetv(db_unique_2,'sta','lat','lon'); % final list of station names, lats and lons to be plotted as points on a map


Output2 = [ lat_TA, lon_TA];

[A9,B9] = size(Output2)





% for j = 2:I 
%     
%     latitude_TA = cell2mat(raw2(j,3));
%     longitude_TA = cell2mat(raw2(j,4));
%     altitude_TA = 1; % some nice big number so anootations don't get gobbled up by mountain ranges and such, not as important for greyscale
% 
%     Output2 = [Output2;[latitude_TA longitude_TA altitude_TA]];
%     
% end

fprintf('Defines the columns in Output2 to be either Latitude or Longitude, assigning them to variables TA_lat_output and TA_long_output \n')

TA_lat_Output = Output2(:,1); % define the TA lat column
TA_lon_Output = Output2(:,2); % define the TA lon column
%altitude_TA_above_map = Output2(:,3); % define the altitude above the topographic map to plot annotations


%%% SECTION 3 - PLOT BOTH SETS OF COORDINATES ON A MAP, AS WELL AS DATA FOR POLITICAL BOUNDARIES, STATES AND COASTLINES

% SETUP THE MAP BASICS

fprintf('Establish the skeleton of the figure that will be used to plot the data acquired \n')

gcf = figure('Color','w','Position',[100 100 1700 900]);

title_string = pfget_string(pf,'stations_alaska');
title(title_string,'FontSize', 27);


ax=usamap(latlim,lonlim); % this is better than specifying the region directly, like 'usamap alaska', because it doesn't lock you in to that projection's boundaries
% worldmap world % or specify which country/regional map to use other than 'world'
axis off


fprintf(['Acquire shape file' shape_file 'to act as map \n'])

canada = shaperead(shape_file,'UseGeoCoords', true, 'BoundingBox', [lonlim', latlim']);
faceColors = makesymbolspec('Polygon',{'INDEX', [1 numel(canada)],'FaceColor', [0.9 0.9 0.9]}); % [0.75 0.75 0.75] is grey, but also hides some stations...
geoshow(ax, canada, 'SymbolSpec', faceColors)

states = shaperead('usastatehi','UseGeoCoords', true, 'BoundingBox', [lonlim', latlim']);

faceColors = makesymbolspec('Polygon',{'INDEX', [1 numel(states)],'FaceColor', [0.9 0.9 0.9]}); % [0.75 0.75 0.75] is grey, but also hides some stations...
geoshow(ax, states, 'SymbolSpec', faceColors)


% PLOT STATION DATA:

fprintf('Convert the variables NWS_lat_Outputs and NWS_long_Output to a projected coordinate system \n')
fprintf('Also convert variables TA_lat_output and TA_long_output to a projected coordinate system ')
% [lat_NWS_projected,lon_NWS_projected] = mfwdtran(NWS_lat_Output,NWS_lon_Output); % Converts the coordinates from stations in order to project them as geographic features to Matlab map coordinates
[lat_TA_projected,lon_TA_projected] = mfwdtran(TA_lat_Output,TA_lon_Output); % Converts the coordinates from stations in order to project them as geographic features to Matlab map coordinates

[lat_NWS_projectedG1,lon_NWS_projectedG1] = mfwdtran(NWS_lat_OutputG1,NWS_lon_OutputG1);


[lat_NWS_projectedG2,lon_NWS_projectedG2] = mfwdtran(NWS_lat_OutputG2,NWS_lon_OutputG2);

[lat_NWS_projectedG3,lon_NWS_projectedG3] = mfwdtran(NWS_lat_OutputG3,NWS_lon_OutputG3);

%Setting up Coordinates for coordinates of cities 

[lat_Cities_Projected,lon_Cities_projected] = mfwdtran(NWS_lat_Output_Cities,NWS_lon_Output_Cities);

hold on;

fprintf('Create a scatter plot with lat_NWS_projected,lon_NWS_projected representing current stations  \n')
fprintf('and lat_TA_projected,lon_TA_projected representing future stations  \n')



for k = 1:(A9-1) % for each row in the lat_TA_projected/lon_TA_projected/dotcolor arrays
    scatter(lat_TA_projected(k,1),lon_TA_projected(k,1),100,'MarkerEdgeColor','k','MarkerFaceColor','w','ZData',10000); % just plot all stations as one for now
end
    for m = 1:(G1-1) % for each row in the lat_NWS_projected/lon_NWS_projected arrays
    
 
    scatter(lat_NWS_projectedG1(m,1),lon_NWS_projectedG1(m,1),50,'MarkerEdgeColor','k','MarkerFaceColor','k','ZData',10000); % plot the NWS stations, the next section is for TA stations
    end
    
    for m = 1:(G2-1) % for each row in the lat_NWS_projected/lon_NWS_projected arrays
    
 
        scatter(lat_NWS_projectedG2(m,1),lon_NWS_projectedG2(m,1),50,'MarkerEdgeColor','k','MarkerFaceColor','k','ZData',altitude_NWS_above_mapG2(m,1)); % plot the NWS stations, the next section is for TA stations
    end
   
   for m = 1:(G3-1) % for each row in the lat_NWS_projected/lon_NWS_projected arrays
    
 
       scatter(lat_NWS_projectedG3(m,1),lon_NWS_projectedG3(m,1),50,'MarkerEdgeColor','k','MarkerFaceColor','k','ZData',altitude_NWS_above_mapG3(m,1)); % plot the NWS stations, the next section is for TA stations
   end


% for j = 1:(G11-1)
%     
%     scatter(lat_Cities_Projected(j,1), lon_Cities_projected(j,1),200,'MarkerEdgeColor','b','MarkerFaceColor','b','ZData',NWS_alt_Output_Cities(j,1));
% end
 
% prompt = 'Do you want to display cities? [Y/N]';
% 
% 
% Cit_Ans = input(prompt,'s');
% 
% Cit_Hypo_Answer = 'Y';
% 
% tf = strcmp(Cit_Ans,Cit_Hypo_Answer);

    for j = 1:(G11-1)
    
    scatter(lat_Cities_Projected(j,1), lon_Cities_projected(j,1),100,'d','MarkerEdgeColor','b','MarkerFaceColor','b','ZData',NWS_alt_Output_Cities(j,1));
    
    dx = 20000; dy=20000;
    
    a = text(lat_Cities_Projected(1,1)+dx, lon_Cities_projected(1,1)+dy,'Anchorage');
    s = a.Color;
    a.Color = 'b';
    b = text(lat_Cities_Projected(2,1)+dx, lon_Cities_projected(2,1),'Juneau');
    s1 = b.Color;
    b.Color = 'b';
    c = text(lat_Cities_Projected(3,1)+dx, lon_Cities_projected(3,1),'Fairbanks');
    s2 = c.Color;
    c.Color = 'b';
    end


% MANUALLY CREATE AND ANNOTATE A LEGEND

fprintf('Create a legend to distinguish between current and future stations \n')

annotation('textbox',[0.69,0.8,0.1,0.1],'String',{'\fontsize{16}        NWS Stations  ','\fontsize{16}    Future TA Stations  ','\fontsize{16}    Current TA Stations  '})
%annotation('textbox',[0.69,0.8,0.1,0.1],'String',{'\fontsize{16}        NWS Stations  ','\fontsize{16}    Future TA Stations  ','\fontsize{16}    Current TA Stations  '})
%scatter(1350000,9701750,20,'MarkerEdgeColor','k','MarkerFaceColor','w'); % 
%scatter(1350000,9636750,20,'MarkerEdgeColor','k','MarkerFaceColor','k');
scatter(1250000,9601750,100,'MarkerEdgeColor','k','MarkerFaceColor','w'); % 
scatter(1250000,9536750,100,'MarkerEdgeColor','k','MarkerFaceColor','k');
grid on;

save_file_string = pfget_string(pf,'save_file_string');
% 
% 
%  set(gcf, 'PaperUnits','inches');
%  set(gcf, 'Units','inches');
%  pos=get(gcf,'Position');
%  set(gcf, 'PaperSize', [pos(3) pos(4)]);
%  set(gcf, 'PaperPositionMode', 'auto');
%  set(gcf, 'PaperPosition',[0 0 5 5]);
%  set( gcf, 'PaperOrientation', 'landscape' ) ;

% % % 
% set(gcf, 'PaperPositionMode', 'manual');
% set(gcf, 'PaperUnits', 'inches');
% set(gcf, 'PaperPosition', [2 2 10 12]);
% % % % 
%  print(save_file_string,'-deps');



%print(gcf, 'test.eps', '-dpsc2', '-r1200', '-noui')
% 
% newname = 'newfilename.png';
% 
% command = sprintf('convert ''%s'' ''%s''', save_file_string, newname);
% system(command); 
% 
% command = sprintf('display ''%s''', newname);
% system(command);

export_fig(save_file_string,'-nocrop')


%open(save_file_string);
%close(gcf);



% exit();
