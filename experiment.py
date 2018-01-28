import random

from learning import read_system
from learning import learn
from learning import diagnose
import types

def generate_random_inputs(system):
    var_to_value = dict()
    for sys_input in system.inputs:
        var_to_value[sys_input] = random.randint(0, 1)
    return var_to_value

def create_training_set(system, training_size, probing="Full"):
    if probing == "Full":
        system.outputs = [component.output for component in system.components.values()]
    else:
        num_of_probes = int(probing)
        potential_probes = system.variables.difference(system.outputs)
        probes = random.sample(potential_probes, num_of_probes)
        system.outputs = system.outputs + probes

    training_set = dict()
    for i in xrange(training_size):
        obs_input = generate_random_inputs(system)
        obs_key = str(obs_input.values())
        while training_set.has_key(obs_key):
            obs_input = generate_random_inputs(system)
            obs_key = str(obs_input.values())

        obs_output = system.propagate(obs_input)
        training_set[obs_key] = (obs_input, obs_output)
    return training_set

def fault(self, inputs):
    output = self.type(inputs)
    return 1-output

def inject_fault(system, faulty_component):
    comp = system.components[faulty_component]
    comp.compute = types.MethodType(fault, comp)




def run_experiment(system, training_size, probing):
    training_set = create_training_set(system, training_size, probing)
    comp_to_behavior = learn(system, training_set)

    # Inject fault
    faults = 1
    faulty_components = random.sample(system.components.keys(), faults)
    for comp in faulty_components:
        inject_fault(system, comp)

    # Create a new instance and propagate its values
    obs_input = generate_random_inputs(system)
    obs_output = system.propagate(obs_input)

    (f, n) = diagnose(comp_to_behavior, obs_input, obs_output)
    #print "Surely faulty"
    surely_faulty = set([c.name for c in f])
    normally_behaving = set([c.name for c in n])
    faulty_components = set(faulty_components)
    #print "Normally behaving"
    #print [c.name for c in n]
    #print "Real faults"
    #print faulty_components

    assert len(surely_faulty.difference(faulty_components))==0 # Surely faulty are really faulty

    # The next assertion is only true because fault now are flips, and are not intermittent
    if len(normally_behaving.intersection(faulty_components))>0:
        print normally_behaving.intersection(faulty_components)
    assert len(normally_behaving.intersection(faulty_components)) == 0  # Normally behaving are not faulty

    identified_faults = surely_faulty.intersection(faulty_components)
    missed_faults = faulty_components.difference(identified_faults)

    return (len(identified_faults),len(missed_faults),len(normally_behaving))

print "System\t #Comps\t Training size\t Probing\t #Experiment\t Identified faults\t Missed faults \t Exonorated"
experiments = 10
probing = "Full"
train_size = 2

for train_size in [2,4,8,16,32,64]:
    for i in xrange(experiments):
        system = read_system("systems/74283.sys") # Must re-read the system so that it returns to normal
        (identified_faults, missed_faults, exonorated_comps)=run_experiment(system,train_size,probing)
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (system.name, len(system.components), train_size, probing, i, identified_faults, missed_faults, exonorated_comps)



