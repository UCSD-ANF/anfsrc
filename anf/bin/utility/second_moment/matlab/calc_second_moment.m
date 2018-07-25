function [G,m2, strike, dip] = calc_second_moment(d, mlats, mlons, melevs, late, lone, depe, Vp, Vs, topl, phas, strike1, dip1, strike2, dip2,matlab_code, temp_dir);
% CALC_SECOND_MOMENT For each fault plane, get partials and run inversion. Return best result.
% Inputs:
%   d       list of time durations; G*m2 =d
%   mlats   list of station latitudes
%   mlons   list of station longitudes
%   melevs  list of station elevations
%   late    event latitude
%   lone    event longitude
%   depe    event depth
%   Vp      P-wave velocity structure
%   Vs      S-wave velocity structure
%   topl    top layer of velocity structure
%   phase   phases of ASTF
%   strike1 strike of fault plane 1
%   dip1    dip of fault plane 1
%   strike2 strike of fault plane 2
%   dip2    dip of fault plane 2
% Outputs:
%   G       partials 
%   m2      second moment
%   strike  strike of fault plane
%   dip     dip of fault plane

strikes = [strike1, strike2];
dips = [dip1, dip2];
n = length(strikes);
Gs = cell(n, 1);
m2s = cell(n, 1);
ssqrs = [];
for i=1:n
    Gs{i}=getpartials_2d_generic(mlats,mlons,melevs,late,lone,depe,Vp,Vs,topl,phas,strikes(i),dips(i),matlab_code, temp_dir);
        
    % Finally do the inversion    
    m = seconds_2d_v2(Gs{i},d');
    m2s{i} = m(1:6);   % Ditch the dummy variable in the decision vector
    % Calculate variance reduction
    ssqrs = [ssqrs, sum((Gs{i}*m2s{i}-d').^2)./sum(d.^2)];  %
end

[min_var, I] = min(ssqrs);
G = Gs{I};
m2 = m2s{I};
strike = strikes(I);
dip = dips(I);
logging.verbose(sprintf('TESTFAULT=1: %s/%s variance reduction is %s. %s/%s variance reduction is %s. Using %s/%s', strike1, dip1, ssqrs(1), strike2, dip2, ssqrs(2), strike, dip))  


