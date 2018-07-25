% runSJFex.m For given orid and set parameters, calculate the second moment and associated errors.
% Inputs:
% From second_moment.xpy
%   db:           database name given by first command-line argument
%   orid:         orid for main-shock event given by second command-line argument
%   select:       regex expression of stations to use
%   reject:       if not None, regex expression of stations to reject
%   filter:       butterworth bandpass filter for waveforms
%   tw:           time window in seconds for windowing waveforms around arrivals
%   loc_margin:   degrees that egf lat/lon can vary from mainshock lat/lon
%   dep_margin:   km that egf depth can vary from mainshock depth
%   time_margin:  time (s) that egf time can vary from mainshock time
%   vel_model:    velocity model
% Outputs:
% To screen - Inversion, Jackknifing, and Bootstrapping if set to 1
% To working directory - orid_egf_setup.mat, orid_egf_measurements.mat
% To image directory - station astf plots, astf fit, final results
% Usage: Runs from second_moment python wrapper
% Exceptions:

% Initiate Antelope-matlab interface.
run('/opt/antelope/5.8/setup.m')

% Figure out how to generalize this
% Add matlab files to MATLABPATH.
% read environmental variable for ANF and append
addpath(genpath(matlab_code));

% Modes to run data in (e.g. verbose, interactively, etc.)
global mode_run;

mode_run = struct('verbose', verbose, 'debug', debug, 'debug_plot', debug_plot, 'interactive', interactive, 'no_figure', no_figure, 'auto_arrival', auto_arrival);
fields = fieldnames(mode_run);
for i=1:numel(fields)
    if strcmp(mode_run.(fields{i}), 'False') == 1
        mode_run.(fields{i}) = false;
    else
        mode_run.(fields{i}) = true;
    end
end
% Add verbosity mode throughout code

% Get mainshock origin, station, arrival information.
db = dbopen(db, 'r');

% Initiate Origin class.
MS = Origin(db, orid, 'MS', fault);
MS = get_stations(MS, select, reject);
MS = get_arrivals(MS, select, reject);
% Set mainshock late, lone, depe for output.
late = MS.eqinfo.elat; lone = MS.eqinfo.elon; depe = MS.eqinfo.edepth;
mage = MS.eqinfo.mag;

% Set strikes and dips for output.
strike1 = MS.eqinfo.strike1; strike2 = MS.eqinfo.strike2;
dip1 =MS.eqinfo.dip1; dip2 = MS.eqinfo.dip2;

% Get all possible egf orids given the conditions.
msorid = orid;

% Determine how to input egf
if egf==-99
    egforids = getEGF(MS, loc_margin, dep_margin, time_margin);
else
    egforids = [egf];
end

% For each EGF possibility, run program.
EGFlen = length(egforids);
for index=1:EGFlen
    orid = egforids(index);
    filename = sprintf('MS%d_EGF%d_setup.mat', msorid, orid);

    % Add a data file flag if want to use specific data file 
    if LOADDATAFILE
        logging.verbose(sprintf('Loading  waveforms from %s', filename))

        try
            load(filename)
        catch
            logging.verbose(sprintf('Filename %s does not exist.', filename))
            logging.die('Check to see if file exists or in correct location.\nRun with -e flag to specify egf orid')
        end            
    else
        logging.verbose(sprintf('Extract waveforms for MSorid %d / EGForid %d', msorid, orid))
        tw = str2num(tw);
        [compm dtsv npEGF npMS slat slon stasm phasem velEGF velMS velEGF_rot velMS_rot timems timeegf duration] ...
                    = data_setup(db, orid, MS, select, reject, filter, tw);
        save(filename, 'compm', 'depe', 'dip1', 'dip2', 'dtsv', 'late', 'lone', 'npEGF', 'npMS', 'slat', 'slon', ...
                    'stasm', 'phasem', 'strike1', 'strike2', 'velEGF', 'velMS', 'timems', 'timeegf', 'duration') 
    end

% Parameters for the PLD measurements of ASTF duration.
    measurements = sprintf('MS%d_EGF%d_measurements.mat', msorid, orid);
    if DOMEAS
    % % call routine to make measurements
        logging.verbose(sprintf('Calculating ASTF measurements for MSorid %d / EGForid %d', msorid, orid))
        [t2,DONE,STF,GFsv,dhatsv,datasv,T,T1sv,epsv,epld,tpld,t1,PhaseSv] ...
                        = makemeasurements(velEGF,velMS,velEGF_rot, velMS_rot, npMS,npEGF,dtsv,stasm, ...
                        compm, phasem, timems,timeegf, duration, NITER, misfit_criteria);
        save(measurements, 't2', 'DONE', 'STF', 'GFsv', 'dhatsv', 'datasv', 'T', 'T1sv', 'epsv', 'epld', 'tpld', 't1', 'PhaseSv')
    else
        logging.verbose(sprintf('Loading ASTF measurements from %s', measurements))
        load(measurements)
    end

    %index of what stations had succesful measurements
    IJ=find(DONE==1);  
    
    %make map of results
    makeresultmap
    
    %plot the individual station summary plots
    makestationplots
%
    if DOINVERSION    
        % Define data vector for inversion; t2 values and phase=P or S
        IJ=find(DONE==1);
        clear d phas mlats mlons melevs
        for i=1:length(IJ)
          ii=IJ(i); 
          mlats(i)=slat(ii); mlons(i)=slon(ii); melevs(i)=0;  % FIX STRUCTURE selev(ii);
          d(i)=t2(ii);
          phas(i)=PhaseSv(ii);
        end

        % Define velocity model for partial calculation
        load(vel_model);
        if ~exist('Vs')
            Vs=Vp/1.73;
        end
        
        % Get partials

        % Get partials and do inversion for both possible fault planes. Select the one with smallest variance. 
        if TESTFAULT
            % get partials, run inversion on both planes, and select best based on variance reduction
            [G, m2, strike, dip] = calc_second_moment(d, mlats,mlons,melevs,late,lone,depe,Vp,Vs,topl,phas,strike1,dip1,strike2,dip2,matlab_code, temp_dir);
        else
            % get partials
            logging.verbose(sprintf('TESTFAULT=0: Using fault plane %d/%d', strike1, dip1))
            [G]=getpartials_2d_generic(mlats,mlons,melevs,late,lone,depe,Vp,Vs,topl,phas,strike1,dip1,matlab_code, temp_dir);
            strike = strike1;
            dip = dip1;

            % do inversion    
            m2=seconds_2d_v2(G,d');
            m2=m2(1:6);   % Ditch the dummy variable in the decision vector
        end

        % variance reduction 
        ssqr=sum((G*m2-d').^2)./sum(d.^2);

        % rupture duration    
        tauc=2*sqrt(m2(1));
        tauc_resids=sum(abs(2*sqrt(G*m2)-2*sqrt(d')));
        tauc_resids_norm=tauc_resids/sum(2*sqrt(d'));

        % u(2,0) - spatial extent of rupture
        X=[m2(4), m2(5); m2(5), m2(6);];

        % Characteristic quantities
        [U,S,V]=svd(X);
        max_ev = max(max(S)); 
        max_ev_ind = find(S == max_ev);
        max_evc = U(:,max_ev_ind);

        if(max_ev_ind == 1);
            min_evc = U(:,2);
        else
            min_evc = U(1,:);
        end

        L_c=2*sqrt(max_ev);
        W_c=2*sqrt(S(2,2));
        
        v0=m2(2:3)/m2(1);
        mv0=sqrt(sum(v0.^2));
        L0=tauc*mv0;
        ratio=L0/L_c;
        ssqr3=sum((G*m2-d').^2)/sum((d'-mean(d)').^2);
        [m2', tauc,L_c,W_c,mv0,L0/L_c, ssqr3];
       
        logging.info('Done with Inversion')
        logging.verbose(sprintf('tau_c %s (s), L_c %s (km), W_c %s (km), mv0 %s (km/s), L0/Lc %s', num2str(tauc,3), num2str(L_c,3), num2str(W_c,3), num2str(mv0,3), num2str(L0/L_c,3)));
  
% testing for station errors, can use this as another way to remove stations 
    %for ii=1:length(IJ)
    %    jG = G;
    %    jG(ii,:) = [];
    %    jD = d';
    %    jD(ii) = [];
    %    m2dum = seconds_2d_v2(jG, jD)
    %    m2d = m2dum(1:6);
    %    mX=[m2d(4), m2d(5); m2d(5), m2d(6);];
    %    [jU,jS,jV] = svd(mX);
    %    L_c_0=2*sqrt(max(max(jS)));
    %    logging.info(sprintf('ii is %s L_c is %s', num2str(ii), num2str(L_c_0)))
    %end 
         
        if DOJACKKNIFE   
            clear mests L_cJK W_cJK vxJK vyJK taucJK
            %if you only want the leave-one-out jacknife, this would suffice
            %jackstat=jackknife(@seconds_2d_v2,G2,dd);     
            %we want to delete all arrivals in a particular azimuth bin
            %following McGuire, Zhao, Jordan, 2001 GJI.  
            % get azimuths
            clear dist az delta
            ns=length(d);
            for ii=1:ns
              [dist(ii),az(ii),delta(ii)] = distaz(late,lone,mlats(ii),mlons(ii)); %lta,lna,ltb,lnb);
            end

            nband=360/azband;
            for ii=1:nband
               az1=(ii-1)*azband; az2=ii*azband;
               IJK=find(az>=az1 & az<=az2);
               Iuse=setdiff([1:ns],IJK);
               G2ii=G(Iuse,:);   d2ii=d(Iuse);
               m2dum=seconds_2d_v2(G2ii,d2ii');
               mests(ii,1:6)=m2dum(1:6);
            end       
            % Get Cij
            clear xcm1bar varjack
            xcm1bar(1:6)=0;
            for i=1:nband
              xcm1bar(1:6)=xcm1bar(1:6)+mests(ii,1:6);
            end
            xcm1bar=xcm1bar/nband;
            varjack=zeros(6,6);
            for ii=1:nband
              clear dum;
              dum=mests(ii,1:6) - xcm1bar;
              varjack=varjack+dum'*dum;
            end
            varjack=varjack/(nband-1);
            %calculates errors on the derived quantities tauc, Lc Wc v0, mv0, L0/Lc
            [sigmatc,sigmaLc,sigmaWc,sigratio,sigv01,sigv02,sigmamV0]=geterrors(m2,varjack);     
                
            logging.info('Done with Jackknifing')
            
            logging.verbose(sprintf('tauc %4.2f+-%3.3f  L_c %4.2f+-%3.2f  W_c %4.2f+-%3.2f  v0 [%4.2f, %4.2f]+-[%3.2f, %3.2f]  mv0  %4.2f+-%3.2f  ratio %4.2f+-%3.2f' ,...
                tauc,sigmatc,L_c,sigmaLc,W_c,sigmaWc,v0(1),v0(2),sigv01,sigv02,mv0,sigmamV0,ratio,sigratio));
        else
            logging.info('DOJACKKNIFE set to 0: Change to 1 to run jackknife')
        end   
        plotresults
      
        if DOBOOTSTRAP
            [mv0u,mv0l,bound2u,bound2l,Lcu,Lcl,taucu,taucl,minvrsv,minvru,minvrl]=bootstrap2nds(G,d,bconf,NB);
            logging.info('Done with Bootstrapping')
            logging.verbose(sprintf('%s confidence limits for tauc (s) [%4.2f,%4.2f],  Lc (km) [%4.2f,%4.2f],  mv0 [%4.2f,%4.2f]',...
                 num2str(bconf), taucl,taucu,Lcl,Lcu,mv0l,mv0u));
        else
            logging.info('DOBOOTSTRAP set to 0: Change to 1 to run bootstrap')
        end
    end
end
