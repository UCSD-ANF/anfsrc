function [t2,DONE,STF,GFsv,dhatsv,datasv,Tsv,T1sv,epsv,epldsv,tpldsv,t1,PhaseSv]=makemeasurements(velEGFa,velMSa,velEGFa_rot, velMSa_rot, npMS,npEGF,dtsva,stasm,compm,phasem, timems,timeegf, duration, niter, misfit_criteria);
ns=size(velEGFa,1);
% ASTF MEASUREMENTS For all stations/channel waveform, calculate ASTF and determine best result per station
% Inputs:
%   velEGFa:            EGF velocity seismograms matrix
%   velMSa:             MS velocity seismograms matrix
%   velEGFa_rot:        rotated EGF velocity seismograms matrix for automated arrival picking
%   velMSa_rot:         rotated MS velocity seismograms matrix for automated arrival picking
%   npMS:               array of points in MS seismograms
%   npEGF:              array of points in EGF seismograms
%   dtsva:              sample frquency of data
%   stasm:              array of stations
%   compm:              array of components
%   phasem:             array of phases
%   timems:             array of MS arrival times relative to window start
%   timeegf:            array of EGF arrival times relative to window start
%   duration:           array of P-S time differences used to determine window length
%   niter:              number of PLD iterations
%   misfit_criteria:    maximum ASTF misfit threshold
% Outputs:
%   t2:                 second moment of RSTF
%   DONE:               0 or 1 to indicate if usable ASTF
%   STF:                array of source time function (STF)
%   GFsv:               EGF (windowed) data matrix
%   dhatsv:             RSTF * EGF data matrix
%   datasv:             MS (windowed) data matrix
%   Tsv:                [T (duration pick) - T1 (arrival - 3 secs)] * dtsva matrix
%   T1sv:               T1 (arrival - 3 secs) * dtsva matrix
%   epsv:               array of misfit of T
%   epldsv:             duration tradeoff matrix
%   tpldsv:             misfit tradeoff matrix
%   t1:                 array mean centroid times
%   PhaseSv:            array of phases

global mode_run
% Will save the measurements in MEASUREMENTS.MAT

% Initialize variables
DONE=zeros(ns,1); logical(DONE);
Npts=2048;
t2(1:ns)=99999; t1(1:ns)=0; t0=t1; dtsv(1:ns)=0;
datasv=zeros(ns,Npts);
dtsv=zeros(ns,1);
dhatsv=zeros(ns,Npts);
GFsv=zeros(ns,Npts);
STF=zeros(ns,Npts);
STF_sm=zeros(size(STF));
Ttsv=zeros(ns,1); 
T1sv=zeros(ns,1);
epsv=zeros(ns,1);
epldsv=zeros(ns,Npts);
tpldsv=zeros(ns,Npts);
Mf(1:ns) = 0;
dofilt=logical(1);   
dtsv=dtsva;


% Automated mode.
if ~mode_run.interactive
    for i=1:ns
        logging.info(sprintf('Running %s_%s_%s ASTF calculation', stasm{i}, compm{i}, string(phasem(i))))
        
        % if EGF and MS samples > 100
        if(npEGF(i)>=100 && npMS(i)>=100)
            % grab MS data
            velMS=velMSa(i,1:npMS(i)); velMS=velMS';
            velMS_rot = velMSa_rot(i,1:npMS(i)); velMS_rot=velMS_rot'; 
            % grab EGF data
            velEGF=velEGFa(i,1:npEGF(i)); velEGF=velEGF';
            velEGF_rot = velEGFa_rot(i,1:npEGF(i)); velEGF_rot=velEGF_rot';
 
            % time from start of waveform
            tms=[1:npMS(i)]*dtsva(i);
            tegf=[1:npEGF(i)]*dtsva(i);
            doi=1;
        else
            doi=0;
        end
        
        if doi == 1;
            % If debug_plot mode, plot EGF and MS data together.
            if mode_run.debug_plot
                figure
                logging.verbose(sprintf('Figure %d: %s_%s_%s MS & EGF Velocity Waveforms', get(gcf,'Number'), stasm{i}, compm{i}, string(phasem(i))))
                plot(tms-tms(1),velMS/max(velMS));
                hold on
                title([stasm{i},'-',compm{i}])
 
                plot(tegf-tegf(1),velEGF/max(velEGF),'r');
                legend('Mainshock','EGF'); xlabel('Time (s)');
                k = waitforbuttonpress;
            end

            % Get samples since waveform start of arrival (8 seconds after start). 
            t = 8./dtsv(i);
        
            % Set MS inversion window.
            % If P phase, set window to end 3 seconds after arrival or to predicted P-S time if less than 3 seconds.
            % Prevents S-wave contamination. 
        
            if strcmp(phasem(i),'P') == 1 & duration(i)
                len = floor(duration(i));
                 if len > 2
                   len = 2;
                 end
            else
                len = 1.5;
            end

            %len = 3; 
            samps_before = 50;
            samps_after = len./dtsv(i);
            [t2(i), DONE(i), STF(i,1:Npts),GFsv(i,1:Npts),dhatsv(i,1:Npts),datasv(i,1:Npts),Tsv(i),T1sv(i),epsv(i),EPLDsv,TPLDsv,t1(i),PhaseSv(i),L_curve_ratio(i)] = astf_calculation(velMS, velEGF, dtsv(i), stasm{i}, compm{i}, phasem(i), t, samps_before, samps_after, Npts, velMS_rot, velEGF_rot, niter, misfit_criteria);
            epldsv(i,1:length(EPLDsv))=EPLDsv;
            tpldsv(i,1:length(TPLDsv))=TPLDsv;
        end; %if
    end %for loop

    % Only use results of apparent duration in 1.5 standard deviation of mean. 
    gids = find(DONE == 1);
    ads = 2*sqrt(t2(gids));
    inds = find(ads > (mean(ads) + 1.0 * std(ads)) | ads < (mean(ads) - 1.0 * std(ads)));
    DONE(gids(inds)) = 0;

    % Flag ones with same station twice, and select the better result.
    good = find(DONE == 1);
    [items, x] = unique({stasm{good}});
    for i=1:length(items)
        ids = find(ismember({stasm{good}}, items(i)));
        if length(ids) > 1
            % normalize apparent duration - mean appr. duration
            % 0 (low deviation) - 1 (large deviation) 
            app_z = normalize(2*sqrt(t2(good))-mean(2*sqrt(t2(good))), ids);
            % normalized misfit
            % 0 (low misfit) - 1 (large misfit)
            m_z = transpose(normalize(epsv(good), ids));
            % normalize l-curve sharpness 
            % 0 (sharp) - 1 (not sharp)
            l_z = normalize(L_curve_ratio(good), ids);
            
            % proxy for quality to compare channels
            tot_z = app_z.*m_z.*l_z;
            [M, I] = max(tot_z); 
            DONE(good(ids(I))) = 0;
        end 
    end
    
    % choose between PFO and TPFO using criteria set above
    good = find(DONE == 1);
    pfo_id = find(ismember({stasm{good}}, 'PFO')); 
    tpfo_id = find(ismember({stasm{good}}, 'TPFO'));
    
    if pfo_id & tpfo_id
        m_z = [epsv(good(pfo_id)) epsv(good(tpfo_id))];
        app_z = normalize(2*sqrt(t2(good)), [pfo_id tpfo_id]);
        l_z = normalize(L_curve_ratio(good), [pfo_id tpfo_id]);
        tot_z = app_z.*m_z.*l_z;
        [M, I] = max(tot_z); 
        if I == 1
            DONE(good(pfo_id)) = 0;
        else
            DONE(good(tpfo_id)) = 0;
        end
    end 

    good = find(DONE == 1);

    logging.info(sprintf('Usable stations: %s', strjoin(strcat({stasm{good}}, '_', {compm{good}}))))

%                  %
% INTERACTIVE MODE %
%                  %


% for each waveform
else
 for i=1:ns
 
  % if EGF and MS samples > 100
  if(npEGF(i)>=100 && npMS(i)>=100)
   % grab MS data
   velMS=velMSa(i,1:npMS(i)); velMS=velMS';
  
   % grab EGF data
   velEGF=velEGFa(i,1:npEGF(i)); velEGF=velEGF';
 
   % time from start of waveform
   tms=[1:npMS(i)]*dtsva(i);
   tegf=[1:npEGF(i)]*dtsva(i);
   doi=1;
  else
   doi=0;
  end
 
  while(doi);
     %whos tms tegf velMS velEGF
  
     % initiate figure
     figure
 
     % plot(time, scaled MS)
     plot(tms-tms(1),velMS/max(velMS));
     hold on
     title([stasm{i},'-',compm{i}])
 
     % plot(time, scaled EGF)
     plot(tegf-tegf(1),velEGF/max(velEGF),'r');
     legend('Mainshock','EGF'); xlabel('Time (s)');
 
     % DONE is 0 to start
     if(DONE(i)==1)
       ipick(i)=menu('THIS ONE IS DONE, REDO?','Yes','No');
     else
       ipick(i)=menu('NOT DONE, Go Ahead w/Decon?','Yes','No');
     end
     close
 
     % if Yes was selected for Decon do the following
     if(ipick(i) == 1) 
     
      % plot MS data
      figure
      plot(velMS)
      title(stasm{i})

%%%%%%%%%%%%%%%%%%%%%%%%%%%
      % extract info from automated waveforms to test code %
 
      % Get samples since waveform start of arrival (8 seconds after start). 
      t = 8./dtsv(i);

      % Set MS inversion window.
      % If P phase, set window to end 3 seconds after arrival or to predicted P-S time if less than 3 seconds.
      % Prevents S-wave contamination. 
      if strcmp(phasem(i),'P') == 1 & duration
          len = floor(duration(i));
           if len > 3
             len = 3;
           end
      else
          len = 3;
      end

      samps_before = 50;
      samps_after = len./dtsv(i);
      win2 = t + samps_after;
      win1 = t - samps_before;

      vline(win2, 'green')
      vline(win1, 'green')
      vline(t, 'red')
%%%%%%%%%%%%%%%%%%%%%%%%%%%
      
      % select window to zoom
      % select at least 50 samples before desired arrivals
      % select ~ 5 seconds after arrival or when amplitude returned to near-zero, do not include later arrivals
      disp('Pick range to Zoom in to')
      [x y] = ginput(1);
      tt1b=round(x);
      [x y]=ginput(1);
      tt2b=round(x);

      % plot MS data from start and end zoom selection
      plot(velMS(tt1b:tt2b))
      title([stasm{i},' ',compm{i}])

      vline(win1-tt1b, 'green')
      vline(win2-tt1b, 'green')
      vline(t-tt1b, 'red') 
      % select range to invert
      % 20-50 samples before first arrival, when ~ 0 amplitude
      % 3-5 seconds after arrival or near zero amplitude
      disp('Pick range to invert')
      [x y] = ginput(1);
      [x2 y2]=ginput(1);
      tt2b=tt1b+round(x2);
      tt1b=tt1b+round(x);
      
      % do not allow data window to be too long, longer than Npts defined above
      if(tt2b-tt1b>=Npts)
       data=velMS(tt1b:tt1b+Npts-1);
      else
       data=velMS(tt1b:tt2b); 
      end
      clf
 
      % plot inversion range data
      plot(data)
      vline(t-tt1b, 'red') 
      % pick arrival time
      disp('Pick P or S-wave arrival time');
      [x y] = ginput(1);
      
      % T1 is arrival - 3 seconds since inversion window
      T1=round(x)-3;
 
      % taper inversion window
      np=length(data);
      zz=taper(np,.1);
      data=data.*zz; 
  
      % add trailing 0s after data until Npts
      data(np+1:Npts)=0;
 
      % new data matrix
      datasv(i,1:Npts)=data';
      close
 
      % plot EGF data
      figure
      plot(velEGF)
      title(strcat('EGF: ', stasm{i}, '-', compm{i}))
      vline(t, 'red') 
      % pick range to zoom, window tightly around arrival
      disp('Pick range to Zoom')
      [x y] = ginput(1);
      tt1b=round(x);
      [x y]=ginput(1);
      tt2b=round(x);
 
      % plot zoom selection
      plot(velEGF(tt1b:tt2b))
      title([stasm{i},' ',compm{i}])
      vline(t-tt1b, 'red')
      % pick arrival time
      disp('Pick P or S wave arrival time')
      [x y] = ginput(1);
      close
      
      % tt1b = arrival time since window beginning
      tt1b=round(x)+tt1b; 
      
      %np comes from Mainshock
      %keyboard
      
      % np = length of inversion window
      % T1 = MS arrival - 3 seconds since inversion window
      np=np-T1;
 
      % tt2b = arrival time + MS inversion window length - (arrival - 3) - 1
      tt2b=tt1b+np-1;
 
      % EGF data is cut to EGF arrival time to tt2b 
      % length(EGF) is length(MS) - T1     
      GF=velEGF(tt1b:tt2b);
 
    if mode_run.debug_plot
        figure
        plot(GF);
        title(strcat('EGF Window: ', stasm{i}, '-', compm{i}))
        k = waitforbuttonpress;
    end

      % do not taper EGF
      zz=taper(np,.1);
      zz(1:np/2)=1;
      %GF=GF.*zz';   % TAPER GF    !!!!! DON"T TAPER GF BECAUSE IT STARTS at 
 %				    %ARRIVAL TIME?
     
      % add trailing 0s after data until Npts
      GF(np+1:Npts)=0;
 
      % new EGF data matrix
      GFsv(i,1:Npts)=GF';
      
      
      % get RSTF
      % inputs MS data, EGF data, T1, number of iterations
      [f,dhat,T,eps,tpld,epld]=pld(data,GF,T1,niter);
 
      % f - RSTF (apparent source time function)
      % dhat - RSTF * EGF (fit to the data seismogram
      % T - duration pick
      % eps - misfit of T
      % tpld - misfit
      % epld - duration tradeoff
 
      % finds 2nd moment of RSTF (t2) and mean centroid time (t1)
      [t2(i),t1(i)]=findt2(f);
      dt=dtsv(i);
      t2(i)=t2(i)*dt*dt;
      STF(i,1:Npts)=f';
      dhatsv(i,1:Npts)=dhat';
      Tsv(i)=(T-T1)*dt;
      T1sv(i)=T1*dt;
      epsv(i)=eps;
      npld=length(tpld);
      epldsv(i,1:npld)=epld(1:npld);
      tpldsv(i,1:npld)=tpld(1:npld);
      %keyboard
 
      % plot the 4 graphs
      figure
      dt=dtsva(i);
      subplot(2,2,1)
 
      % plot MS data
      plot([1:length(data)]*dt,data/max(data),'k'); hold on;
 
      % plot EGF data
      plot(dt*t1(i)+[1:length(GF)]*dt,GF/max(GF),'r');
      %xlim([0,length(data)*dt])
      xlim([0 5]); ylim([-1.1 1.1]);
      xlabel('Time (s)')
      legend('Data','EGF');
      title([stasm{i},' ',compm{i}]);  
      
      % plot ASTF
      subplot(2,2,2)
      plot([1:length(STF(i,:))]*dt,STF(i,:)); hold on;
      xlabel('Time (s)')
      title(['ASTF, moment:',num2str(sum(STF(i,:)),5)]);
      plot(t1(i)*dt,STF(round(t1(i))),'*')
      ylim([0 1.05*max(STF(i,:))])
      text(.1,.8*max(STF(i,:)),['ApprDur:',num2str(2*sqrt(t2(i)),2),' s'])
      xlim([0 2.1*t1(i)*dt]);
      %xlim([0,3*T1sv(i)])
 
      % plot misfit     
      subplot(2,2,3)
      plot(tpld*dt,epld); hold on;
      xlabel('Time (s)');
      ylabel('Misfit');
      xlim([0 3*t1(i)*dt])
      [junk,ind]=min(abs(tpld-T));
      plot(tpld(ind)*dt,epld(ind),'*')
      ylim([0 1])
      
      % plot seismogram fit
      subplot(2,2,4)
      plot([1:length(data)]*dt,data,'k')
      hold on
      plot([1:length(dhat)]*dt,dhat,'r')
      legend('Data','EGF*STF')
      title(['Seismogram Fit']);
      %xlim([0,length(data)*dt])
      xlim([0 5]);
      xlabel('Time (s)')
      
      l_curve_ratio(i) =(epld(npld) - epld(ind))/(tpld(npld) - tpld(ind)) * (tpld(ind) - tpld(1))/(epld(ind) - epld(1)); 
      % decide whether result is worth saving
      savei=menu('SAVE THIS RESULT','Yes P-wave','Yes S-wave', 'No REDO IT','No done');
      if(savei==1)
          DONE(i)=1;
          PhaseSv(i)='P';
          doi=0;
      elseif(savei==2);
          DONE(i)=1;
          PhaseSv(i)='S';
          doi=0;
      elseif(savei==3)
          DONE(i)=0;
          doi=1;
      elseif(savei==4)
          DONE(i)=0;
          doi=0;
      end
     
    end %ipick
     
  end; %while
  
  %%%% at the end of each station, save progress
  logging.verbose(['Done with ',stasm{i},' ',compm{i},' Saving to MEASUREMENTS.mat']);
  save('MEASUREMENTS.mat','DONE','Npts','t2','t1','datasv','dtsv','dhatsv','GFsv',...
      'STF','STF_sm','Tsv','T1sv','epsv','epldsv','tpldsv');
 
 end  % stations
    % Only use results of apparent duration in 1.5 standard deviation of mean. 
    gids = find(DONE == 1);
    ads = 2*sqrt(t2(gids));
    inds = find(ads > (mean(ads) + 1.0 * std(ads)) | ads < (mean(ads) - 1.0 * std(ads)));
    DONE(gids(inds)) = 0;

    % Flag ones with same station twice, and select the better result.
    good = find(DONE == 1);
    [items, x] = unique({stasm{good}});
    for i=1:length(items)
        ids = find(ismember({stasm{good}}, items(i)));
        if length(ids) > 1
            % normalize apparent duration - mean appr. duration
            % 0 (low deviation) - 1 (large deviation) 
            app_z = normalize(2*sqrt(t2(good))-mean(2*sqrt(t2(good))), ids);
            % normalized misfit
            % 0 (low misfit) - 1 (large misfit)
            m_z = transpose(normalize(epsv(good), ids));
            % normalize l-curve sharpness 
            % 0 (sharp) - 1 (not sharp)
            l_z = normalize(l_curve_ratio(good), ids);
            
            % proxy for quality to compare channels
            tot_z = app_z.*m_z.*l_z;
            [M, I] = max(tot_z); 
            DONE(good(ids(I))) = 0;
        end 
    end
    
    % choose between PFO and TPFO using criteria set above
    good = find(DONE == 1);
    pfo_id = find(ismember({stasm{good}}, 'PFO')); 
    tpfo_id = find(ismember({stasm{good}}, 'TPFO'));
    
    if pfo_id & tpfo_id
        m_z = [epsv(good(pfo_id)) epsv(good(tpfo_id))];
        app_z = normalize(2*sqrt(t2(good)), [pfo_id tpfo_id]);
        l_z = normalize(l_curve_ratio(good), [pfo_id tpfo_id]);
        tot_z = app_z.*m_z.*l_z;
        [M, I] = max(tot_z); 
        if I == 1
            DONE(good(pfo_id)) = 0;
        else
            DONE(good(tpfo_id)) = 0;
        end
    end 

    good = find(DONE == 1);

    logging.info(sprintf('Usable stations: %s', strjoin(strcat({stasm{good}}, '_', {compm{good}}))))

end %interactive vs automated if statements
logging.verbose('DONE MAKING ASTF MEASUREMENTS')

           %%% PHASE PICKER TO IMPROVE ARRIVAL TIMES %%%
    
           % testing parameters
           % if strcmp(phasem(i), 'P')
           %     xis = [0.001 0.1 0.3 0.5 0.7 0.9 0.999];
           %     bins = [10 25 50 100]
           %     for x = xis
           %         Tn = 0.01;
           %         xi = x;
           %         
           %         for b = bins
           %             nbins = b;
           %             o = 'to_peak';
           %             type = 'na';
           %             pflag = 'Y';
           %             try
           %                 [loc, snr_db] = PhasePicker(velMS_rot((tt1b):tt2b), dtsv(i), type, pflag, Tn, xi, nbins, o);
           %             catch
           %                 'Cannot run picker'
           %             end
           %             if loc >= 0
           %                 [xi, nbins]
           %                 k = waitforbuttonpress
           %             end
           %         end
           %         % if new arrival was selected update waveform window 
           %     end 
           % end
            
           % testing best parameters
           % if strcmp(phasem(i), 'P')
           %     xis = [0.001 0.1 0.3 0.5 0.7 0.9 0.999];
           %     bins = [10 25 50 100]
           %     for x = xis
           %         Tn = 0.01;
           %         xi = x;
           %         
           %         for b = bins
           %             nbins = b;
           %             o = 'to_peak';
           %             type = 'na';
           %             pflag = 'Y';
           %             try
           %                 [loc, snr_db] = PhasePicker(velEGF_rot((tt1b-samps_before):tt2b), dtsv(i), type, pflag, Tn, xi, nbins, o);
           %             catch
           %                 'Cannot run picker'
           %             end
           %             if loc >= 0
           %                 [xi, nbins]
           %                 k = waitforbuttonpress
           %             end
           %         end
           %         % if new arrival was selected update waveform window 
           %     end
           % end 
