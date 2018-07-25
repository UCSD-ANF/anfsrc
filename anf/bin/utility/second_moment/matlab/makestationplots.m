% script to plot individual station results of the deconvolution

for ii=1:length(IJ)
    i=IJ(ii);
    data=datasv(i,:);
    GF=GFsv(i,:);
    %STF=STFsv(IJ(i),:);
    dhat=dhatsv(i,:);
    npld=max(find(epld(i,:)>=.0001));

    if mode_run.debug_plot
        figure;
    end    

    dt=dtsv(i);
    subplot(2,2,1)
    plot([1:length(data)]*dt,data/max(data),'k'); hold on;
    plot(dt*t1(i)+[1:length(GF)]*dt,GF/max(GF),'r');
    %xlim([0,length(data)*dt])
    xlim([0 3.5]);
    xlabel('Time (s)')
    legend('Data','EGF');
    title([stasm{i},' ',compm{i}])
 
    subplot(2,2,2)
    plot([1:length(STF(i,:))]*dt,STF(i,:)); hold on;
    xlabel('Time (s)')
    title(['ASTF moment:',num2str(sum(STF(i,:)))]);
    plot(t1(i)*dt,STF(round(t1(i))),'*')
    ylim([0 1.05*max(STF(i,:))])
    text(.1,.8*max(STF(i,:)),['\tau_c(s): '])
    text(.1,.7*max(STF(i,:)),[num2str(2*sqrt(t2(i)),2),' s'])
    xlim([0,3.5*T1sv(i)])
 
    subplot(2,2,3)
    plot(tpld(i,1:npld)*dt,epld(i,1:npld)); hold on;
    xlabel('Time (s)');
    ylabel('Misfit');
    xlim([0 3*t1(i)*dt])
    [junk,ind]=min(abs(tpld(i,1:npld)*dt-(T1sv(i)+T(i))));
    plot(tpld(i,ind)*dt,epld(i,ind),'*')
    ylim([0 1])
    xlim([0.25 3])
 
    subplot(2,2,4)
    plot([1:length(data)]*dt,data,'k')
    hold on
    plot([1:length(dhat)]*dt,dhat,'r')
    legend('Data','EGF*STF')
    title(['Seismogram Fit']);
    %xlim([0,length(data)*dt])
    xlim([0 4]);
    xlabel('Time (s)')
    hold off
    % consider a temp folder for any images that aren't final    

    if mode_run.debug_plot
        k = waitforbuttonpress;
    else
        set(gcf, 'visible', 'off')
        set(gcf, 'pos', [10 10 900 500])
    end
    
    if ~mode_run.no_figure
        saveas(gcf, sprintf('%s/MS%d_EGF%d_%s_%s_ASTFresult.png', image_dir, msorid, orid, stasm{i}, compm{i}))
    end
    close

end

