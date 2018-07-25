% script to make a little map of the results
tauc=2*sqrt(t2); taucmed=median(tauc(IJ));

if mode_run.debug_plot
    figure;
end
    
scatter(slon(IJ),slat(IJ),100,2*sqrt(t2(IJ)),'filled'); hold on;
set(gcf, 'Visible', 'off')
colormap(jet); colorbar; caxis([.9*min(tauc(IJ)) 1.1*max(tauc(IJ))])
plot(lone,late,'k^','MarkerSize',15,'MarkerFaceColor','r'); hold on;
%text(slon, slat, stasm)
axis([-117.0 -115.9 33.0 34.1])
axis('equal')
clear Xf Yf

for ii=1:length(IJ);
    [Xf(ii), Yf(ii)] = ds2nfu(slon(IJ(ii)), slat(IJ(ii))); % GET EM ALL FIRST IN FULL AXES
end

Npts=size(STF,2);
for ii=1:length(IJ)
    subaxes2=axes('Position',[Xf(ii) Yf(ii) 0.08 0.13]);
    t=[0:(dtsv(IJ(ii))):(Npts-1)*(dtsv(IJ(ii)))];
    plot(t,STF(IJ(ii),:),'k','LineWidth',1); axis('off'); hold on;
    x1=t1(IJ(ii))*(dtsv(IJ(ii)))-2*taucmed;
    x2=t1(IJ(ii))*(dtsv(IJ(ii)))+3*taucmed;
    xlim([x1, x2]); %ylim([0 45]);
end

% Figure out how to run now plot on figure
if mode_run.debug_plot
    k = waitforbuttonpress;
else
    set(gcf, 'visible', 'off')
    set(gcf, 'pos', [10 10 900 500])
end

if ~mode_run.no_figure
    saveas(gcf, sprintf('%s/MS%d_EGF%d_ASTFresult.png', image_dir, msorid, orid));
end
close 
