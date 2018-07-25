function  [G,toa] = getpartials_2d_generic(mlats,mlons,melevs,late,lone,depe,Vp,Vs,topl,phas,strike,dip,matlab_code, temp_dir);
%
%   Calculates the G matrix for the second moments inversion for a known 2D fault
%   Gm=d  where m is the six independent second moments [tt, xt, yt, xx,xy, yy];
%   INPUTS
%   mlats, mlons are the lat-lons of each measurement station ordered same
%       as your data vector
%   late,lone,depe are the earthquake location
%   Vp, Vs, topl are the 1D velocity model, topl is top of each layer in km
%   phas is 'P' or 'S' for each measurement, same order as your data vector
%   strike, dip are the fault plate
%
%   OUTPUTs
%   G = partials for 2D fault ordered as
%        partials(nmeas,1)=1;         %Time -- Time
%        partials(nmeas,2)=-2*s(1);   %Along-Strike -- Time
%        partials(nmeas,3)=-2*s(3);   %Downdip -- Time
%        partials(nmeas,4)=s(1)*s(1); %Along-Strike -- Along-Strike
%        partials(nmeas,5)=s(1)*s(3); %Along-Strike --  DownDip
%        partials(nmeas,6)=s(3)*s(3); %Downdip -- Downdip
%
%   See McGuire, 2004, BSSA for details
% no checks of input yet
logging.verbose(sprintf('Running topp to get partials'))
setenv('GFORTRAN_STDIN_UNIT', '5') 
setenv('GFORTRAN_STDOUT_UNIT', '6') 
setenv('GFORTRAN_STDERR_UNIT', '0')
nmeas=length(mlats);
NL=length(Vp);
topl=topl';

partials=zeros(nmeas,6);
rsv=zeros(nmeas,3);
rsv2=zeros(nmeas,3);
toa=zeros(nmeas,1);
delta=zeros(nmeas,1);
az=zeros(nmeas,1);
tt=zeros(nmeas,1);


olat=mean(mlats);
olon=mean(mlons);
origin=[olat, olon];
llh=[mlats; mlons; melevs;];
xy_sta = llh2localxy(llh, origin);
x_sta=xy_sta(:,1); y_sta=xy_sta(:,2);
[dum]=llh2localxy([late,lone,0]',origin);
xe=dum(1); ye=dum(2);


for i=1:nmeas

 % get inputs for raytrace code;
 % delta (km), depth, nl, V, top
 az(i)=azimuth(late,lone,mlats(i), mlons(i));
  %[x_sta,y_sta]=convert(mlats,mlons,olat,olon);
 %[xe,ye]=convert(late,lone,olat,olon);
 delta(i)=sqrt((x_sta(i)-(xe))^2 + (y_sta(i)-(ye))^2);
 depth=depe;
 phasi=' ';
 if(char(phas(i))=='P')
   V=Vp';
 elseif(char(phas(i))=='S')
   V=Vs';  
 else
   disp(['Problem with Phase for station',num2str(i)])
 end
 % Have everything now
 %keyboard
 ddum=delta(i);
 %ddum
 %make input for raytrace code	and run and readin outputs
    save('toppinputs', 'ddum', 'depth', 'NL', 'V', 'topl', '-ascii')
    %keyboard
    % FOR LINUX THE FOLLOWING IS FINE TO RUN FORTRAN CODES
    logging.verbose(sprintf('Running topp to get raytrace for station %0.2f degrees from event', az(i)))
    cmd = sprintf('export DYLD_LIBRARY_PATH=""; %s/bin/topp', matlab_code);
    unix(cmd);
    % FOR MAC YOU NEED THE SETENV lines up above and 
    %[status, result] = system(['export DYLD_LIBRARY_PATH="";' '%s', cmd)]);
    % to run the program topp because of a disagreement between gfortran
    % and matlab about where stdout is,....
    %keyboard
	fid=fopen('toppoutputs');
	tt(i)=fscanf(fid,'%g',1);
	toa(i)=fscanf(fid,'%g',1);
    fclose(fid);
	
    %toa
% THEN GET UNIT VECTOR ALONG RAY
	%horiz component
	rh=sin(toa(i)*pi/180);
	rv=cos(toa(i)*pi/180);  %z positive down
	rsv(i,3)=rv;
	rsv(i,1)=rh*sin(az(i)*pi/180);  %x positive east
    rsv(i,2)=rh*cos(az(i)*pi/180);  %y positive north
	
% THEN GET VP
%find vp  % this is actually the velocity at the epicenter for the current
%phase P or S
	ii=0;
	ct=0;
	vp=0;
	while(ct ~= 1)
 	 ii=ii+1;
 	 if(topl(ii) >= depe)
 	  ct=1;
 	  vp=V(ii-1);
 	 end
    end
	
    %vp
	s=(1/vp)*[rsv(i,1),rsv(i,2), rsv(i,3)]';  % slowness vector
	% now rotate to [Along strike, fault normal, DownDip]	
	zz=strike-90;
	zz=zz*pi/180;
	rotm=[cos(zz), -sin(zz),  0;
	      sin(zz), cos(zz), 0;
	      0,	0,	 1;];
	s=rotm*s;
	zz=dip-90;
	zz=zz*pi/180;
	rotm=[1, 0, 0;
	      0, cos(zz), sin(zz);
	      0, -sin(zz), cos(zz);];	
	s=rotm*s;
	rsv2(i,1:3)=vp*s';   %Unit Vector in Rotated Coords
	ssv(i,1:3)=s';	

% THEN CALCULATE PARTIALS SIMPLE AS THAT
        partials(i,1)=1;         %Time -- Time
        partials(i,2)=-2*s(1);   %Along-Strike -- Time
        partials(i,3)=-2*s(3);   %Downdip -- Time
        partials(i,4)=s(1)*s(1); %Along-Strike -- Along-Strike
        partials(i,5)=s(1)*s(3); %Along-Strike --  DownDip
        partials(i,6)=s(3)*s(3); %Downdip -- Downdip
end
G=partials;

topout = sprintf('%s/toppoutputs', temp_dir)
topin = sprintf('%s/toppinputs', temp_dir)
unix(sprintf('mv toppoutputs %s', topout))
unix(sprintf('mv toppinputs %s', topin))
 
%keyboard
end
