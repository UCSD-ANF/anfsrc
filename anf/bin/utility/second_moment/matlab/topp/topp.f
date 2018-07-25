	program topp
	
		
		
	real  v(100)
	real top(100)
	integer nl
	real t
	real ain
	real depth
	real delta
	
	open(12,file='toppinputs',status='old')
	rewind 12
	read(12,*)delta
	read(12,*)depth
	read(12,*)rnl
	nl=int(rnl)
	do i=1,nl
	 read(12,*)v(i)
	enddo
	do i=1,nl
	 read(12,*)top(i)
	enddo
	close(12)
			
	write(6,*)'calling ttime',delta,depth,nl,v,top
		
	call ttime(delta, depth, nl, v, top, t, ain)
	
	write(6,*)'out of ttime',t
	write(6,*)'out of ttime',ain
	
	open(12,file='toppoutputs',status='unknown')
	rewind 12
	write(12,*)t
	write(12,*)ain
	

	end
