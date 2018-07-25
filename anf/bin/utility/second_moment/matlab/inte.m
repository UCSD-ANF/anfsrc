function	[y]=inte(x,dt);

% Trapeziodal rule integration
% from L. J. Wang, Caltech Thesis 1996.
% EERL 96-04  Processing of Near-Field Earthquake
% Accelerograms,  Pasadena CA September 1996
dt2=dt/2; y(1)=0;
for i=2:length(x)
 y(i)=y(i-1)+(x(i-1)+x(i))*dt2;
end
y=y';
return
