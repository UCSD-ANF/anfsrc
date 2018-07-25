function [t2, done, stf,gfsv,dhatsv,datasv,tsv,t1sv,epsv,epldsv,tpldsv,t1,phasesv,l_curve_ratio] = astf_calculation(velMS, velEGF, dt, sta, comp, phase, t, samps_before, samps_after, Npts, velMS_rot, velEGF_rot, niter, misfit_criteria, update_arrival)
% ASTF CALCULATION for a given station
% Inputs:
%   velEGF:             EGF velocity seismogram
%   velMS:              MS velocity seismogram
%   velEGF_rot:         rotated EGF velocity seismogramfor automated arrival picking
%   velMS_rot:          rotated MS velocity seismogram for automated arrival picking
%   dt:                 data frequency (inverse of sample rate)
%   tms:                MS arrival time
%   tegf:               EGF arrival time
%   sta:                station
%   comp:               component
%   phase:              phase
%   t:                  arrival time since start of window
%   samps_before:       samples before arrival time
%   samps_after:        samples after arrival time
%   Npts:               number of points in seismogram 
%   niter:              number of PLD iterations
%   misfit_criteria:    maximum ASTF misfit threshold
%   update_arrival:     flag to turn on/off automated arrival detection
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
    % set defaults for optional parameters
    if nargin < 14
        logging.die('Not enough input arguments in astf_calculation')
    elseif nargin == 14
        update_arrival = 0;
    elseif nargin > 15
        logging.die('Too many input arguments in astf_calculation')
    end  

    tt2b = t + samps_after;
    tt1b = t - samps_before;
    if update_arrival
        if strcmp(phase, 'P')
            xi = 0.5;
            nbins = [25 50 100 2/dt];
            s = 0;
        end

        if strcmp(phase, 'S')
            xi = 0.99;
            nbins = [10 15 20 50];
            s = 30;
        end
        [tt1b tt2b] = automated_arrival(xi, nbins, s, phase, 'MS', velMS_rot, tt1b, tt2b, samps_before, samps_after, dt);
        t = tt1b + samps_before;
    end

    if mode_run.debug_plot
        figure
        logging.verbose(sprintf('Figure %d: %s_%s_%s Mainshock Velocity Waveform', get(gcf,'Number'), sta, comp, string(phase)))
        plot(velMS);
        hold on
        vline(tt1b,'green')
        hold on
        vline(tt2b, 'green')
        hold on
        vline(t, 'red')
        title(strcat('MS: ', sta, '-', comp))
        k = waitforbuttonpress;
    end

    % Do not allow data window to be too long, longer than Npts defined above.
    if(tt2b-tt1b>=Npts)
        data=velMS(tt1b:tt1b+Npts-1);
    else
        data=velMS(tt1b:tt2b);
    end
    clf
    
    if mode_run.debug_plot
        figure
        logging.verbose(sprintf('Figure %d: %s_%s_%s Mainshock Inversion Window', get(gcf,'Number'), sta, comp, string(phase)))
        plot(data);
        hold on
        vline(50, 'red')
        title(strcat('MS Window: ', sta, '-', comp))
        k = waitforbuttonpress;
    end

    % T1 is arrival - 3 seconds since inversion window
    T1=samps_before - 3;

    % taper inversion window
    np=length(data);
    zz=taper(np,.1);
    data=data.*zz;

    % add trailing 0s after data until Npts
    data(np+1:Npts)=0;

    % new data matrix
    datasv(1:Npts)=data';

    % np = length of inversion window
    % T1 = MS arrival - 3 seconds since inversion window
    np=np-T1;

    % tt1b = arrival time since window beginning
    % tt2b = arrival time + MS inversion window length - (arrival - 3) - 1
    tt1b = t;
    tt2b=tt1b+np-1;
    
    if update_arrival
        if strcmp(phase, 'P')
            xi = 0.5;
            nbins = [25 50 100 2/dt];
            s = 0;
        end

        if strcmp(phase, 'S')
            xi = 0.99;
            nbins = [10 15 20 50];
            s = 30;
        end
        [tt1b tt2b] = automated_arrival(xi, nbins, s,  phase, 'EGF', velMS_rot, tt1b, tt2b, samps_before, samps_after, dt, np);
    end

    if mode_run.debug_plot
        figure
        logging.verbose(sprintf('Figure %d: %s_%s_%s EGF Velocity Waveform', get(gcf,'Number'), sta, comp, string(phase)))
        plot(velEGF);
        hold on
        vline(tt1b, 'green')
        vline(tt2b, 'green')
        title(strcat('EGF: ', sta, '-', comp))
        k = waitforbuttonpress;
    end

    % EGF data is cut to EGF arrival time to tt2b 
    % length(EGF) is length(MS) - T1     
    GF=velEGF(tt1b:tt2b);

    if mode_run.debug_plot
        figure
        logging.verbose(sprintf('Figure %d: %s_%s_%s EGF Inversion Window', get(gcf, 'Number'), sta, comp, string(phase)))
        plot(GF);
        title(strcat('EGF Window: ', sta, '-', comp))
        k = waitforbuttonpress;
    end
    % do not taper EGF
    zz=taper(np,.1);
    zz(1:np/2)=1;

    % add trailing 0s after data until Npts
    GF(np+1:Npts)=0;

    % new EGF data matrix
    gfsv(1:Npts)=GF';

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
    [t2,t1]=findt2(f);
    t2=t2*dt*dt;
    stf(1:Npts)=f';
    dhatsv(1:Npts)=dhat';
    tsv=(T-T1)*dt;
    t1sv=T1*dt;
    epsv=eps;
    npld=length(tpld);
    epldsv(1:npld)=epld(1:npld);
    tpldsv(1:npld)=tpld(1:npld);
    [junk,ind]=min(abs(tpld-T));
    phasesv = phase;
 
    l_curve_ratio =(epld(npld) - epld(ind))/(tpld(npld) - tpld(ind)) * (tpld(ind) - tpld(1))/(epld(ind) - epld(1)); 
    if epld(ind) > misfit_criteria && ~update_arrival && mode_run.auto_arrival
        logging.verbose(sprintf('Misfit %0.2f > Criteria %0.2f: Attempting to detect arrival to improve result', epld(ind), misfit_criteria)) 
        update_arrival = 1;
        [t2,done,stf,gfsv,dhatsv,datasv,tsv,t1sv,epsv,epldsv,tpldsv,t1,phasesv] = astf_calculation(velMS, velEGF, dt, sta, comp, phase, t, samps_before, samps_after, Npts, velMS_rot, velEGF_rot, niter, misfit_criteria, update_arrival);
         
    else
        if mode_run.debug_plot
            % plot the 4 graphs
            figure
            logging.verbose(sprintf('Figure %d: %s_%s_%s ASTF Results', get(gcf,'Number'), sta, comp, string(phase)))
            subplot(2,2,1)

            % plot MS data
            plot([1:length(data)]*dt,data/max(data),'k'); hold on;

            % plot EGF data
            plot(dt*t1+[1:length(GF)]*dt,GF/max(GF),'r');
            %xlim([0,length(data)*dt])
            xlim([0 5]); ylim([-1.1 1.1]);
            xlabel('Time (s)')
            legend('Data','EGF');
            title([sta,'-',comp]);

            % plot ASTF
            subplot(2,2,2)
            plot([1:length(stf(:))]*dt,stf(:)); hold on;
            xlabel('Time (s)')
            title(['ASTF, moment:',num2str(sum(stf(:)),5)]);
            plot(t1*dt,stf(round(t1)),'*')
            ylim([0 1.05*max(stf(:))])
            text(.1,.8*max(stf(:)),['ApprDur:',num2str(2*sqrt(t2),2),' s'])
            xlim([0 2.1*t1*dt]);
            %xlim([0,3*T1sv(i)])

            % plot misfit     
            subplot(2,2,3)
            plot(tpld*dt,epld); hold on;
            xlabel('Time (s)');
            ylabel('Misfit');
            xlim([0 3*t1*dt])
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

            k = waitforbuttonpress;
            close all
        end

        logging.verbose(sprintf('Misfit: %0.2f ', epld(ind)))
        logging.verbose(['Apparent Duration: ', num2str(2*sqrt(t2),2), ' s'])
        logging.verbose(['ASTF Moment: ', num2str(sum(stf(:)),5)])

        if epld(ind) > misfit_criteria
            logging.info(sprintf('DO NOT USE %s_%s_%s: Misfit %.2f > Criteria %.2f', sta, comp, string(phase), epld(ind), misfit_criteria))
            done = 0;
        else
            done = 1;
        end
    end

