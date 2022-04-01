### Artifical Intelligence: Fuzzy Scheduler

This program implements a fuzzy scheduler, which is a type of Constraint Satisfaction Problem (CSP). CSPs are an important class of problems in artificial intelligence. 

Since the scheduler is 'fuzzy', it allows some tasks to be delayed; this incurs a specified cost per hour of delay. We have to design a schedule that minimises this cost. This makes it a subclass of CSPs called Constraint Optimization Problems (COP), since we have to optimise based on various constraints to minimise the cost.

The tasks take a certain duration, have various constraints defined on when they can start and end, as well as dependencies on other tasks. Some tasks have hard deadlines, meaning they cannot be delayed (or the cost is infinite).

The main code is in aFuzzyScheduler.py. Two sample input files are also provided. 

**Usage:**

`python aFuzzyScheduler.py inputfile.txt`

The above is a summary, the Specification.PDF has detailed information on the problem.

To adhere closely to CSP conventions, the program uses some helper files from AIPython.org and modifies them to suit our purpose. The main fuzzy scheduler above has been completely built from scratch.

**Example**

An example input file is below. The program can run much longer and complex files. It can be used to form practical schedules. Ref the task specification for more details.

```
#four tasks with long durations and no domain constraints, but binary constraints that force them to run on different days

task, weld_chassis 8
task, tweak_axle 7
task, vulcanise_rubber 8
task, test_bulletproof_tyres 8

#binary constraints
constraint, weld_chassis before tweak_axle
constraint, test_bulletproof_tyres after vulcanise_rubber
constraint, tweak_axle before vulcanise_rubber

#soft constraints
domain, test_bulletproof_tyres ends-by thu 4pm 300
```

This would give the result:
```
weld_chassis:mon 9am
tweak_axle:tue 9am
vulcanise_rubber:wed 9am
test_bulletproof_tyres:thu 9am
cost:300
```
