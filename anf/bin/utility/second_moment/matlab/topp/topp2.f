	program top
	
		
		
	real  v(12)
	real top(12)
	integer nl
	real t
	real ain
	real depth
	real delta
	
	delta=.1 
	depth=5	
	v(1)=1
	v(2)=2
	v(3)=3
	v(4)=4
	v(5)=5
	v(6)=6
	v(7)=7
	v(8)=8
	v(9)=9
	v(10)=10
	v(11)=11
	v(12)=12
	top(1)=0
	top(2)=2
	top(3)=4
	top(4)=6
	top(5)=8
	top(6)=10
	top(7)=12
	top(8)=14
	top(9)=16
	top(10)=18
	top(11)=20
	top(12)=22
	nl=12
		
		
	write(6,*)'calling ttime',delta,depth,nl,v,top
	call ttime(delta, depth, nl, v, top, t, ain)
	
	write(6,*)'out of ttime',t
	write(6,*)'out of ttime',ain

	end
