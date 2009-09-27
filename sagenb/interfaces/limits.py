class ProcessLimits:
    """
    INPUT:
    
        - ``max_vmem`` -- maximum virtual memory available to worksheet
          process in megabytes, e.g., 500 would limit worksheet to
          use 500 megabytes.

        - ``max_cputime`` -- maximum cpu time in seconds available to
          worksheet process.  After this amount of cputime is used,
          the worksheet process is killed.

        - ``max_walltime`` -- maximum wall time in seconds available
          to worksheet process. After this amount of time elapses, the
          worksheet subprocess is killed.

        - ``max_processes`` -- maximum number of processes the
          worksheet process can create
    """
    def __init__(self,
                 max_vmem=None,     # maximum amount of virtual memory available to the shell in megabytes
                 max_cputime=None,  # maximum cpu time in seconds
                 max_walltime=None, # maximum wall time in seconds
                 max_processes=None,
                 ):
        self.max_vmem = max_vmem
        self.max_cputime = max_cputime
        self.max_walltime = max_walltime
        self.max_processes = max_processes

    def __repr__(self):
        return 'Process limit object:' + \
               '\n\tmax_vmem = %s MB'%self.max_vmem +  \
               '\n\tmax_cputime = %s'%self.max_cputime + \
               '\n\tmax_walltime = %s'%self.max_walltime + \
               '\n\tmax_processes = %s'%self.max_processes
    
                 
