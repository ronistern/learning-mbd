import random

from learning import read_system
from learning import learn
from learning import diagnose
from learning import fully_observed_subsystems
import types
import math

def generate_random_inputs(system):
    var_to_value = dict()
    for sys_input in system.inputs:
        var_to_value[sys_input] = random.randint(0, 1)
    return var_to_value

def create_training_set(system, training_size):
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



def add_probes(system, probing):
    potential_probes = system.variables.difference(system.outputs).difference(system.inputs)
    if probing == "Full":
        probes = potential_probes
    else:
        num_of_probes = int(probing)
        probes = random.sample(potential_probes, num_of_probes)
    probes = list(probes)
    system.outputs = system.outputs + probes
    assert len(set(system.outputs).intersection(system.inputs))==0 # Verify that we only probe the non-input variables

    return probes

def run_experiment(system_file, training_size, probing, faults):
    system = read_system(system_file)  # Must re-read the system so that it returns to normal
    probes = add_probes(system, probing)

    training_set = create_training_set(system, training_size)

    # Inject fault that causes an abnormal behavior
    while True:
        faulty_components = set(random.sample(system.components.keys(), faults))
        for comp in faulty_components:
            inject_fault(system, comp)

        # Create a new instance and propagate its values
        obs_input = generate_random_inputs(system)
        obs_output = system.propagate(obs_input)

        normal_system = read_system(system_file)
        normal_system.outputs = normal_system.outputs + probes
        normal_output = normal_system.propagate(obs_input)

        if obs_output!=normal_output:
            break
        else:
            system = normal_system

    (candidate_faults, exonorated) = diagnose(system,training_set,obs_input,obs_output)

    assert_candidate_faults(candidate_faults,faulty_components)
    assert_exonorated(exonorated, faulty_components)

    identified_faults = faulty_components.intersection(candidate_faults)
    missed_faults = faulty_components.difference(candidate_faults)
    false_positives = candidate_faults.difference(faulty_components)

    return (system, len(identified_faults),len(missed_faults),len(exonorated),len(false_positives))


def assert_candidate_faults(candidate_faults, faulty_components):
    if len(candidate_faults)>0:
        assert len(candidate_faults.intersection(faulty_components))>0

def assert_exonorated(exonorated, faulty_components):
    assert len(exonorated.intersection(faulty_components)) == 0






def sample_complexity():
    print "system\t probing\t subsystems\t sub-inputs\t m"
    experiments = 100
    for probing in [1, 2, 4, 8, 16, "Full"]:
        for i in xrange(experiments):
            system = read_system("systems/74181.sys")
            add_probes(system, probing)
            subsystems = fully_observed_subsystems(system)
            num_of_subsystems = len(subsystems)
            max_inputs = max([len(subsystem.inputs) for subsystem in subsystems.values()])

            sv = math.pow(2, max_inputs) * num_of_subsystems
            epsilon = 0.1
            delta = 0.1
            m = sv / epsilon * math.log(sv / delta)

            print "%s\t %s\t %s\t %s\t %s" % (system.name, probing, num_of_subsystems, max_inputs, m)

def run_all_experiments():
    print "System\t #Comps\t Training size\t Probing\t #Experiment\t Identified faults\t Missed faults \t Exonorated\t False Positives"
    experiments = 100
    faults = 1
    for probing in [1,2,4,8,16,"Full"]:
        for train_size in [512,1024,2048]:
            for i in xrange(experiments):
                system_file = "systems/74181.sys"
                (system, identified_faults, missed_faults, exonorated_comps,false_positives)=run_experiment(system_file,train_size,probing,faults)
                print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (system.name, len(system.components), train_size, probing, i, identified_faults, missed_faults, exonorated_comps,false_positives)

                # system_file = "systems/74283.sys"
                # (identified_faults, missed_faults, exonorated_comps,false_positives)=run_experiment(system,train_size,probing)
                # print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (system.name, len(system.components), train_size, probing, i, identified_faults, missed_faults, exonorated_comps,false_positives)


