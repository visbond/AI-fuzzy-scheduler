# fuzzyScheduler.  Ref readme for spec and other details
# A Fuzzy scheduler schedules tasks allowing for some delays and their associated costs
# Total cost has to be minimised. A Constraint Optimization Problem

# This program was written in the early days when I was new to Python. 
# It does the job and does it efficiently, but is not very object-oriented. 
# If I wrote it today, a lot of functionality would be encapsulated in class methods.

from sys import argv
from copy import deepcopy # got side effects when working on a dictionary, so using deep copy

'''Reads an input file and returns the tokens in it as nested lists'''
def readfile (filename):
    infile = open(filename) #mode is read only by default 
    # print("DEBUG Opened file:", infile) #DEBUG. To show filename
    line_of_tokens = []	#will hold tokens on one line
    file_of_tokens = []	#will hold all token lines (i.e. collect the above)
    i,j = 0,0	#DEBUG
    for line in infile:
        if line[0] == '#' or line == '\n': #comment or blank line
            continue	#restart loop, skipping the line
        #if is not a commented line, extract tokens from it
        line = line.rstrip('\n') 	
        tokens = line.split(' ')
        i+=1	#DEBUG
        #print(line, end = '')	#DEBUG. to ensure tokens below completely cover line
        line_of_tokens = []	#will hold tokens of this line, reset before every new line
        for token in tokens:
            #print(token)	#DEBUG
            line_of_tokens.append(token)
            j+=1	#DEBUG
        file_of_tokens.append(line_of_tokens)

    infile.close()
    return file_of_tokens
#end def readfile()

#some variables declared globally to make it easier to use across functions
#and to save space on stack, since lists and dictionaries can grow large

week_days = ['mon','tue','wed','thu','fri']
named_hours = ['9am','10am','11am','12pm','1pm','2pm','3pm','4pm','5pm']

#the following defines all possible values in the domain, from Monday 9 am to Friday 5pm
#Monday 12am (00:00) is taken as the start of the counter (time 0), and hours are 
#added throughout the entire week continuously. This makes < or > calculations natural
week_numeric_hours = {	'mon':[9,10,11,12,13,14,15,16,17],	#times on Monday, in 24h clock
            'tue':[33,34,35,36,37,38,39,40,41], #times on Tuesday, continuing from previous day. 33 is 9am (24+9 = 33)
            'wed':[57,58,59,60,61,62,63,64,65], #Wednesday. 57 is 9am (48+9 = 57)
            'thu':[81,82,83,84,85,86,87,88,89],	#Thursday
            'fri':[105,106,107,108,109,110,111,112,113]}	#Friday

tasks_and_durations = {}  # holds task names and time taken by each task
tasks_sorted = []   # purely so have exact order in which tasks appear in input, since output must be in same order
task_domains = {}   # will hold the domain of each task (same format as for CSP argument)
constraints_bin = []    # holds binary constraints
soft_constraints = {}   # holds soft constraints
unary_constraints = {}   # will hold a task's unary constraints in one place so domain updation can be done together


'''Returns the entire domain from mon 9am to fri 5pm, as a set'''
def FullDomain():
    return {d+' '+t for d in week_days for t in named_hours} 
#end def FullDomain()


'''Creates a domain of days and times from a range passed to it, both ends inclusive'''
'''for example, if passed wed 11am, thu 4pm, would return a set with {wed 11am, wed 12pm...wed 5pm, thu 9am...thu 4pm}'''
def BuildDomainFromDayTime(start_day, start_time, end_day, end_time):
    # print("DEBUG Build Day Time Domain from", start_day, start_time, end_day, end_time)
    d1 = week_days.index(start_day)
    t1 = named_hours.index(start_time)
    d2 = week_days.index(end_day)
    t2 = named_hours.index(end_time)
    domain = set()
    
    for i in range (t1,len(named_hours)):   # times on start day, from start time
        domain.add(start_day+' '+named_hours[i])
    
    for i in range (d1+1, d2):  # all times for the days in between
        domain.update({week_days[i]+' '+t for t in named_hours})
    
    for i in range (t2+1):  #last day. Ending time is inclusive, so must add 1 to the range
        domain.add(end_day+' '+named_hours[i])
    
    return domain
#end def BuildDomainFromDayTime()


'''builds domain from single time (used in four kinds of unary constraints, starts-before <time>, starts-after, ends-before, ends-after)
this function works with start_time and assumes default case of start-before. For start-after, the second parameter is true
For end-before/after, the calling function will do the task duration adjustment and send the appropriate start-time'''
def BuildDomainFromTime(start_time, after=False):
    if after is False: # starts-before
        tlimit = named_hours.index(start_time)
        domain = {d+' '+named_hours[t] for d in week_days for t in range(tlimit+1)} # have to go to range (..+1) because this start-time is included
        # print("DEBUG starts-before time case. Time and constrained domain is", start_time, domain)
        return domain
    else:   # starts-after
        tlimit = named_hours.index(start_time)
        domain = {d+' '+named_hours[t] for d in week_days for t in range(tlimit,len(named_hours))}
        # print("DEBUG starts-after time case. Time and constrained domain is", start_time, domain)
        return domain
#end def BuildDomainFromTime()    


'''Subtracts duration (in hours) from time (in '3pm', '10am' type format) to return time in same format
e.g. for arguments (3pm, 2), will return 1pm. Has bounds check'''
def Subtract(hour, duration):
    # print("DEBUG in Subtract with time and duration", hour, duration)
    current_time = named_hours.index(hour)
    new_index = current_time - int(duration)
    if new_index < 0:   # duration is too long and takes index to before 9am upon subtraction
        # print("DEBUG ERROR SUBTRACT INDEX OUT OF RANGE")
        return 'err'
    return named_hours[new_index]
#end def Subtract()


'''Adds duration in hours to time. e.g. (3pm, 2) will return 5pm. Has bounds check'''
def Add (hour, duration):
    current_time = named_hours.index(hour)
    new_index = current_time + int(duration)
    if new_index > 8: #bounds crossed
        # print("DEBUG ERROR ADD INDEX OUT OF RANGE")
        return 'err'
    return named_hours[new_index]
#end def Add()


'''Applies unary constraints to the tasks and prunes their domains accordingly'''
def PruneDomains(unary_constraints):
    for task in unary_constraints:
        current_task_cons = unary_constraints[task] # just to make it easier to understand. Get list of constraints for this task from dictionary
        # print("\nDEBUG Working on unary constraints for", task)
        
        for constraint in current_task_cons: # now traverse across list of constraints for this task

            if (len(constraint) == 1): # is a single day or single time constraint
                if constraint[0].isalpha(): # is a single day name
                    const_domain = {constraint[0]+' '+t for t in named_hours}   # create constrained domain of time slots for just this day (e.g. fri 9am..fri 5pm)
                    task_domains[task].intersection_update(const_domain)    # intersect with existing domain to reduce values
                    
                else: # is a single time
                    const_domain = {d+' '+constraint[0] for d in week_days}   # create domain of this time slot for all days (e.g. mon 3pm..fri 3pm)
                    task_domains[task].intersection_update(const_domain)   

            elif (len(constraint) == 2): # is a starts-before <time>, ends-before <time> type of constraint
                if constraint[0] == 'starts-before':
                    const_domain = BuildDomainFromTime(constraint[1])
                    task_domains[task].intersection_update(const_domain)   
                elif constraint[0] == 'starts-after':
                    const_domain = BuildDomainFromTime(constraint[1], True)
                    task_domains[task].intersection_update(const_domain)
                elif constraint[0] == 'ends-before':
                    start_time = Subtract(constraint[1],tasks_and_durations[task]) # get start time by subtracting duration from end time
                    if start_time == 'err': #duration is too long to be accommodated
                        return True # indicates error
                    const_domain = BuildDomainFromTime(start_time)
                    task_domains[task].intersection_update(const_domain)
                else:   # is ends-after case
                    start_time = Subtract(constraint[1],tasks_and_durations[task])
                    if start_time == 'err': #duration is too long to be accommodated
                        return True # indicates error
                    const_domain = BuildDomainFromTime(start_time, True)
                    task_domains[task].intersection_update(const_domain)
            
            elif len(constraint) == 3: # starts/ends before/after <day> <time>
                if constraint[0] == 'starts-before':
                    const_domain = BuildDomainFromDayTime('mon','9am',constraint[1], constraint[2]) # from beginning of week to given day time
                    task_domains[task].intersection_update(const_domain)   
                elif constraint[0] == 'starts-after':
                    const_domain = BuildDomainFromDayTime(constraint[1], constraint[2], 'fri', '5pm') # from given day time to end of week
                    task_domains[task].intersection_update(const_domain)
                elif constraint[0] == 'ends-before':
                    start_time = Subtract(constraint[2],tasks_and_durations[task]) # get start time by subtracting duration from end time
                    if start_time == 'err': #duration is too long to be accommodated
                        return True # indicates error
                    const_domain = BuildDomainFromDayTime('mon','9am',constraint[1], start_time)
                    task_domains[task].intersection_update(const_domain)
                else:   # is ends-after case
                    start_time = Subtract(constraint[2],tasks_and_durations[task])
                    if start_time == 'err': #duration is too long to be accommodated
                        return True # indicates error
                    const_domain = BuildDomainFromDayTime(constraint[1], start_time, 'fri', '5pm')
                    task_domains[task].intersection_update(const_domain)
            
            else:   #longest cases, of in a day-time range between two given values
                start_day = constraint[1]
                start_time = constraint[2].split('-')[0]
                end_day = constraint[2].split('-')[1]
                end_time = constraint[3]
                # print("DEBUG in day-time range case, constraint is", constraint)
                if constraint[0] == 'starts-in':
                    const_domain = BuildDomainFromDayTime(start_day, start_time, end_day, end_time)
                    task_domains[task].intersection_update(const_domain)
                else: # 'ends-in'
                    start_time = Subtract(start_time, tasks_and_durations[task]) # get start time by subtracting duration from given time
                    end_time = Subtract(end_time, tasks_and_durations[task])
                    if start_time == 'err' or end_time == 'err': #duration is too long to be accommodated in range
                        return True # indicates error
                    const_domain = BuildDomainFromDayTime(start_day, start_time, end_day, end_time)
                    task_domains[task].intersection_update(const_domain)

    return False # indicates domains were pruned without encountering any error
#end def PruneDomains()


'''Parses lines (lists) already read from the input file and puts them into task,
 constraint, domain, or soft-constraint data structures'''
def ParseLine(line):
    # line[1] is task name
    if line[0] == "task,":
        tasks_and_durations[line[1]]=line[2]   #add task key to dictionary, with value the number of hours it takes
        tasks_sorted.append(line[1])
    elif line[0] == "constraint,":
        if line[2] == "same-day":   # replace - by _, so it can be used directly as a function name by CSP
            line[2] = "same_day"
        elif line[2] == "starts-at":
            line[2] = "starts_at"
        constraints_bin.append([(line[1],line[3]),line[2]]) #e.g. would add [(t1,t2),'before']
    elif line[0] == "domain,":
        if line[2] == "ends-by":    #is a soft constraint
            soft_constraints[line[1]] = [(line[3],line[4]),line[5]] # {task: [(day, time), cost]}
        else:   #is a hard domain constraint
            if line[1] not in unary_constraints:
                unary_constraints[line[1]] = [] # create new dictionary key if doesn't exist
            line.pop(0) # remove the word 'domain' from the beginning
            task = line.pop(0) # is already the dictionary key name, so not needed
            unary_constraints[task].append(line) # save it for now, will handle all unary constraints together 
            # since there may be multiple domain constraints for a task across multiple lines, with each requiring different operations
#end def parseLine()


# condition-defining functions for Constraint class objects

'''t1 ends when or before t2 starts.
Since t1's duration needs to be known beforehand, so creating function inside function, like ne_ and is_ in cspExamples.py'''
def before_template (duration):
    def before(t1, t2):  
        # print("DEBUG in before with t1 duration and assignments",  duration, t1, t2)
        day1 = t1.split()[0]
        time1 = t1.split()[1]
        day2 = t2.split()[0]
        time2 = t2.split()[1]
        if week_days.index(day1) < week_days.index(day2):
            return True # no need to check time if day is earlier 

        elif week_days.index(day1) > week_days.index(day2):
            return False # no need to check time if day is later

        else:   # days are same, must compare times
            endtime1 = Add(time1,duration)
            if endtime1 == 'err': #has exceeded bound, invalid value
                # print("DEBUG BOUNDS EXCEEDED IN ADD VIA BEFORE FUNCTION")
                return False

            if named_hours.index(endtime1) <= named_hours.index(time2):
                return True
            else:
                return False
    #end def inner before()

    before.__name__ = "before function, for duration "+str(duration) # name of the inner function, needed for some CSP displays

    return before
# end def before_template()
        

'''t1 starts after or when t2 ends. t2's duration must be known to do the calculation, 
so using a function generating template that takes the duration as an argument'''
def after_template(duration):

    def after (t1,t2):
        day1 = t1.split()[0]
        time1 = t1.split()[1]
        day2 = t2.split()[0]
        time2 = t2.split()[1]

        if week_days.index(day1) > week_days.index(day2): #no need to check time if day is afterwards
            return True

        elif week_days.index(day1) < week_days.index(day2):
            return False

        else:   # days are same, times must be compared
            endtime2 = Add(time2, duration)               
            if endtime2 == 'err': #has exceeded bound, invalid value
            #    print("DEBUG BOUNDS EXCEEDED IN ADD VIA AFTER FUNCTION")
               return False
            if named_hours.index(endtime2) <= named_hours.index(time1):
                return True
            else:
                return False
    # end def inner after()
    after.__name__ = "after function, for duration "+str(duration)
    return after
#end outer def after_template()


'''t1 starts exactly when t2 ends
t2's duration is passed to the function-generating template'''
def starts_at_template(duration):
    def starts_at (t1, t2):
        day1 = t1.split()[0]
        time1 = t1.split()[1]
        day2 = t2.split()[0]
        time2 = t2.split()[1]

        if week_days.index(day1) != week_days.index(day2): #no need to check time if days are not the same
            return False

        else:   # days are same, times must be compared
            endtime2 = Add(time2, duration)               
            if endtime2 == 'err': #has exceeded bound, invalid value
            #    print("DEBUG BOUNDS EXCEEDED IN ADD VIA STARTS-AT FUNCTION")
               return False
            if named_hours.index(endtime2) == named_hours.index(time1):
                return True
            else:
                return False
    #end inner def starts_at()

    starts_at.__name__ = "starts-at function, for duration "+str(duration) # name of the inner function, needed for some CSP displays

    return starts_at
# end outer def starts_at_template()
    

'''t1 and t2 are scheduled on the same day'''
def same_day (t1, t2):
    day1 = t1.split()[0]
    day2 = t2.split()[0]
    if day1 == day2:
        return True
    return False
#end def same_day()


'''used to calculate the cost of a soft constraint. If day & hour are before the deadline, 
returns 0, else returns the number of hours by which the task is late (taking full day as 24 hours)'''
def hours_late (start_day, start_hour, deadline_day, deadline_hour, duration):
    difference = week_numeric_hours[start_day][named_hours.index(start_hour)] + int(duration) - week_numeric_hours[deadline_day][named_hours.index(deadline_hour)]
    if difference > 0:
        return difference
    else:
        return 0
#end def hours_late()


'''works on final goal assignments found by searching the state space
to minimize the cost'''
def optimize_constraints (assignments):
    mincost = 9999999 # assigning very large initial value, to calculate minimum
    assign_index = 0 # will hold index of the task assignment that has minimum total cost
    for assign in assignments: #a row of one assignment of all tasks
        ass = deepcopy(assign) #had gotten side effects earlier with popping one value affecting another
        totalcost = 0   #will hold the total cost due to lateness of all tasks in this assignment
        for task in ass:
            if task not in soft_constraints: # there is no soft constraint on this task
                continue
            cost = soft_constraints[task][1]
            soft_day = soft_constraints[task][0][0] # day and time are stored as a tuple
            soft_time = soft_constraints[task][0][1]
            assign_slot = ass[task].pop() # is a backup copy, so popping has no side-effects
            ass_day, ass_time = assign_slot.split()[0], assign_slot.split()[1]
            lateness_cost = int(cost) * hours_late(ass_day, ass_time, soft_day, soft_time, tasks_and_durations[task])
            totalcost += lateness_cost
        #end inner for
        if totalcost < mincost:
            mincost = totalcost
            assign_index = assignments.index(assign)
    #end outer for
    return (mincost, assign_index)
#end def optimize_constraints()


from cspProblem import CSP, Constraint
from cspConsistency import Search_with_AC_from_CSP
from searchGeneric import AStarSearcher


#main starts here	
if __name__ == "__main__":
    file_of_tokens = readfile(argv[1])

    #parse the lines read from the file and build task and constraints data structure from them
    for line in file_of_tokens:
        ParseLine(line)

    for task in tasks_and_durations:   #initialise full domain for all tasks, will prune later
        task_domains[task] = FullDomain() # will 'multiply' days and times to create max possible domain,
        # a set of all possible time slots e.g. mon 9am, mon 10am ... fri 4pm, fri 5pm

    global_ending_constraint = ['ends-before', '5pm'] # all tasks must finish on the same day. So add to all tasks before domains pruned
    for task in tasks_and_durations:
        if task not in unary_constraints.keys():
            unary_constraints[task] = []
        unary_constraints[task].append(global_ending_constraint)

    errflag = PruneDomains(unary_constraints)
    if errflag is True:
        print('No Solution')
        
    if errflag is False:
        for task in task_domains:   # check if any domain has already become empty on applying unary constraints. Don't need to go further in that case
            if(task_domains[task] == set()):    # empty set
                errflag = True
                print('No Solution')
                break

    if errflag is False:
        constraints_CSP = []    # will hold binary constraints in CSP's constructed format
        for con in constraints_bin:
            if con[1] == "before":
                t1_duration = tasks_and_durations[con[0][0]] # get task 1 from tuple and its duration
                constraints_CSP.append(Constraint(con[0], before_template(t1_duration))) 
            elif con[1] == "after":
                t2_duration = tasks_and_durations[con[0][1]] # get task 2 from tuple and its duration
                constraints_CSP.append(Constraint(con[0], after_template(t2_duration)))
            elif con[1] == "starts_at":
                t2_duration = tasks_and_durations[con[0][1]] # get task 2 from tuple and its duration
                constraints_CSP.append(Constraint(con[0], starts_at_template(t2_duration)))
            else:   # is same_day. Function of same name is defined, and templates not needed, so using directly
                constraints_CSP.append(Constraint(con[0], eval(con[1]))) # eval turns it to function from string

        taskCSP = CSP(task_domains, constraints_CSP)
        AStarSearcher.max_display_level = 0
        searcherA = AStarSearcher(Search_with_AC_from_CSP(taskCSP))

        while searcherA.search() is not None:
            continue
        
        if searcherA.goalpaths == []:
            errflag = True
            print("No Solution")
            
    if errflag is False:
        (cost, assignment_index) = optimize_constraints(searcherA.goalpaths)
        
        # print in the required order
        for task in tasks_sorted:
            row = deepcopy(searcherA.goalpaths[assignment_index]) # the dictionary contains sets, and have gotten side-effects when popping earlier
            print(task, ':', row[task].pop(), sep = '')

        print("cost:",cost, sep = '')




