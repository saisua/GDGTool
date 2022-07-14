import dispy

# function 'compute' is distributed and executed with arguments
# supplied with 'cluster.submit' below
def compute(n):
    import time, socket
    time.sleep(n)
    host = socket.gethostname()
    return (host, n)

if __name__ == '__main__':
    # executed on client only; variables created below, including modules imported,
    # are not available in job computations
    import random
    # distribute 'compute' to nodes; in this case, 'compute' does not have
    # any dependencies to run on nodes
    cluster = dispy.JobCluster(compute)
    # run 'compute' with 20 random numbers on available CPUs
    jobs = []
    for i in range(5):
        job = cluster.submit(random.randint(5,20))
        jobs.append(job)
    # cluster.wait() # waits until all jobs finish
    for job in jobs:
        host, n = job() # waits for job to finish and returns results
        print('%s executed job %s at %s with %s' % (host, job.id, job.start_time, n))
        # other fields of 'job' that may be useful:
        # job.stdout, job.stderr, job.exception, job.ip_addr, job.end_time
    cluster.print_status()  # shows which nodes executed how many jobs etc.