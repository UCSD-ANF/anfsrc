	function[f]= posproj(g,T1,T)
%   Enforce positivity on the ASTF
%
	f=zeros(size(g));
	for i=1:length(g)
	 if(i>=T1 & i<=T & g(i)>=0)
	   f(i)=g(i);
	 else
	   f(i)=0;
	 end
	end
	
