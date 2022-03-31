### Artifical Intelligence: Fuzzy Scheduler

This program implements a fuzzy scheduler, which is a type of Constraint Satisfaction Problem (CSP). CSPs are an important class of problems in artificial intelligence. 

Since the scheduler is 'fuzzy', it allows some tasks to be delayed, which incurs a specified cost per hour of delay. We have to design a schedule that minimises this cost. This makes it a subclass of CSPs called Constraint Optimization Problems (COP), since we have to optimise based on various constraints to minimise the cost (while completing all tasks if possible).

The tasks take a certain duration, have various constraints defined on when they can start and end, as well as dependencies on other tasks. Some tasks have hard deadlines, meaning they cannot be delayed (or the cost is infinite).

The main code is in fuzzyScheduler.py. Two sample input files are also provided. 

Usage:

`python fuzzyScheduler.py inputfile.txt`

The above is a summary, the Specification.PDF has detailed information on the problem.

To adhere closely to CSP conventions, the program uses some helper files from AIPython.org and modifies them to suit our purpose. The main fuzzy scheduler above has been completely built from scratch.