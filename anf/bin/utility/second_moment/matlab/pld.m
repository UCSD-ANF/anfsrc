function[RSTF,dhat,T,eps,t,e]= pld(data,GF,T1,niter)
% DOES THE PLD inversion process for the RSTF from a data seismogram
% and a GF seismogram.   The P or S-wave seismograms are expected to be 
% alligned so that the P-wave arrival time occurs in the sample
% T1, and the GF begins at the P-wave arrival time.
% Also, it is assumed that they have been padded with zeros to
% a sufficient length of time to avoid wrap-arounds. (i.e. more than
% double).  T-T1 is the estimate of the duration of the STF
% you pick fromt the misfit tradeoff curve.
% niter is the number of iterations (ie inverse damping)
% 
%   The returned variables are:
%   RSTF  the apparent source time function
%   dhat  the fit to the data seismogram (RSTF*GF)
%   T     the duration pick
%   eps   the misfit at T
%   t,e   the misfit vs duration tradeoff curve
%
%  This follows Bertero et al. 1997, Lanza et al. 1999, and McGuire 2004,
%  see manual for references.
	global mode_run
	N=length(data);
	e0=(T1)/N;
	epsilon=e0:.005:0.4;	
	ne=length(epsilon);
	e=zeros(ne,1);
	t=zeros(ne,1);	
	foldt=zeros(N,1);
	fnewt=zeros(N,1);
	fneww=fft(fnewt);
	GT=zeros(N,1);
	dataw=fft(data);
	GFw=fft(GF);
	Gstarw=conj(GFw);
	tau=max(abs(GFw));
	tau=tau^2;
	tau=1/tau;
	
	for i=1:N
	 GT(i)=GF(N-i+1);
	end;
	GTw=fft(GT);	
	nit=niter;
% LOOP OVER EPSILONS
	
	for i=1:ne	   
	   eps=epsilon(i);
	   T=round(eps*N);
	   t(i)=T;
	   %set up inverse problem	
	   	   
	   % iterate over n
	   for j=1:nit
	     foldt=fnewt;
	     foldw=fneww;
	     clear dum
	     f=fft(foldt);
	     res=dataw-GFw.*f;
	     dum=Gstarw.*res;
	     gneww=foldw+tau.*dum;
	     gnewt=real(ifft(gneww));
	     fnewt=posproj(gnewt,T1,T);
	     fneww=fft(fnewt);
	   end
	   % end iterations for this T.	   
       dhat=real(ifft(fneww.*GFw));
	   
	   sum1=0; sum2=0;
	   for j=1:N
	    sum1=sum1+(data(j)-dhat(j))^2;
	    sum2=sum2+(data(j))^2;
	   end
	   e(i)=sum1/sum2;
	end
	
% plot eps vs T
    % find the t,e values that minimize difference to origin (i.e. L-curve corner)
    tnorm = (t - min(t))/(max(t)- min(t));
    enorm = (e - min(e))/(max(e) - min(e));
    dist = sqrt(tnorm.^2 + enorm.^2);
    
    [M,I] = min(dist);
    T = t(I);

    if mode_run.interactive
        figure
	    plot(t,e)
	    ylabel('Epsilon')
	    xlabel('T')
        hold on
        scatter(t(I), e(I), 'filled', 'r')

	    axis([0 round(epsilon(end)*N) 0 1])
        
        disp('Pick T')
        [x y] = ginput(1);
        T=round(x);
        hold off
        close
    end

	% iterate over n
	foldt=zeros(N,1);
	fnewt=zeros(N,1);
	fneww=fft(fnewt);
	for j=1:nit
	     foldt=fnewt;
	     foldw=fneww;
	     clear dum
	     f=fft(foldt);
	     res=dataw-GFw.*f;
	     dum=Gstarw.*res;
	     gneww=foldw+tau.*dum;
	     gnewt=real(ifft(gneww));
	     fnewt=posproj(gnewt,T1,T);
	     fneww=fft(fnewt);
	 end
	     
	dhat=real(ifft(fneww.*GFw));
	RSTF=fnewt;
	sum1=0; sum2=0;
	   for j=1:N
	    sum1=sum1+(data(j)-dhat(j))^2;
	    sum2=sum2+(data(j))^2;
	   end
	   eps=sum1/sum2;
    
