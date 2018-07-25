%function [t2,t1,t0]=findt2(STF,plott2);
function  [t2,t1]=findt2(STF);  
% FINDT2 finds the 2nd moment of a RSTF (t2) and mean/centroid time (t1)
% Inputs:
%   STF:         source time function vector.
%   IF plott2=1  plot the time function and let you pick the start
%                and endpoints to integrate over.   
%   IF plott2=0  assumes the whole time function is relaible and integrates
%                from start to end of the array.
% Outputs:
%   t2:         second moment of RSTF
%   t1:         mean/centroid time

% If plott2 not given, set to 0
if nargin < 1
    logging.die('Not enough input arguments in findt2')
elseif nargin == 1
    plott2 = 0;
elseif nargin > 2
    logging.die('Too many input arguments in findt2')
end 

if(plott2)
 figure
 plot(STF)
 axis([0 round(.5*length(STF)) 0 max(STF)])
 disp('Pick lefthand point to start variance calculation at')
 [x y] = ginput(1);
 I1=round(x);
 disp('Pick righthand point to end variance calculation at')
 [x y] = ginput(1);
 I3=round(x);
else
 I1=1;
 I3=length(STF);
end


% moment and centroid
msum=0; tsum=0;
%STF=STF-min(X,Z);
for i=I1:I3;
  msum=msum+STF(i);
  tsum=tsum+STF(i)*i;
end

%second moment
t0=tsum/msum;
t1=tsum/msum;
tsum=0;
for i=I1:I3
  tsum=tsum+STF(i)*(i-t0)^2;
end 

t2=tsum/msum;

if(plott2)
 hold on;
 plot(t0,STF(round(t0)),'*')
 axis([0 700 0 max(STF)])
 pause(0.2);
 close
end

return
end
