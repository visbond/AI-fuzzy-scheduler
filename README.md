### Artifical Intelligence: Fuzzy Scheduler

Scheduling tasks efficiently is important in many fields, from phone operating systems to megafactories. This program implements a fuzzy scheduler. Unlike a conventional scheduler, a fuzzy scheduler allows some tasks to be delayed, with each hour (or any time unit) of delay incurring a specified cost. Such a fuzzy scheduler is a type of Constraint Satisfaction Problem (CSP). CSPs are an important class of problems in artificial intelligence. 

Since each time-unit of delay incurs a cost, we have to design a schedule with the least cost. This makes it a subclass of CSPs called Constraint Optimization Problems (COP), since we have to optimise based on various constraints to minimise the cost.

The tasks take a certain duration, have various constraints defined on when they can start and end, as well as dependencies on other tasks. Some tasks have hard deadlines, meaning they cannot be delayed (or the cost is infinite).

The main code is in aFuzzyScheduler.py. Two sample input files are also provided. 

**Usage:**

`python aFuzzyScheduler.py inputfile.txt`


The above is a summary, the Specification.PDF has detailed information on the problem.

To adhere closely to CSP conventions, the program uses some helper files from AIPython.org and modifies them to suit our purpose. The main fuzzy scheduler above has been completely built from scratch.

This program was written in the early days when I was new to Python. It does the job and does it efficiently, but is not very object-oriented. If I wrote it today, a lot of functionality would be encapsulated in class methods.

**Example**

Two simple examples are given below. The program can run much longer and more complex files. It can be used to form practical schedules. Ref the task specification PDF for more details.

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

Another example with more types of constraints:

```
#three tasks with three binary constraints, multiple domain constraints for each task, and soft deadlines
#t1, t2 etc can be any arbitrary tasks
task, t1 3
task, t3 2
task, t2 4

#three binary constraints
constraint, t1 before t2
constraint, t3 starts-at t2
constraint, t3 after t2

#domain constraint
domain, t2 ends-after mon 2pm
domain, t2 starts-before 4pm
domain, t2 starts-after 10am
domain, t2 wed
domain, t1 ends-before 1pm
domain, t1 starts-after 10am
domain, t3 starts-in tue 12pm-wed 3pm
domain, t3 ends-in tue 5pm-wed 5pm

#soft deadlines
domain, t1 ends-by tue 3pm 40
domain, t2 ends-by wed 1pm 10
```
This gives the resulting schedule:

```
t1:mon 10am
t3:wed 2pm
t2:wed 10am
cost:10
```
