import random
import json
from systems import System

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

def assert_candidate_faults(candidate_faults, faulty_components):
    if len(candidate_faults)>0:
        assert len(candidate_faults.intersection(faulty_components))>0

def assert_exonorated(exonorated, faulty_components):
    if len(exonorated.intersection(faulty_components)) != 0:
        print "ex: %s, faulty: %s" % (exonorated, faulty_components)
    assert len(exonorated.intersection(faulty_components)) == 0


'''
Create random sets of inputs, to be used to create the training set
'''
def choose_system_inputs(system, training_size):
    training_inputs = dict()
    previously_created_inputs = set()
    input_index = 0
    for i in xrange(training_size):
        obs_input = generate_random_inputs(system)
        obs_key = json.dumps(obs_input)
        while obs_key in previously_created_inputs:
            obs_input = generate_random_inputs(system)
            obs_key = json.dumps(obs_input)
        training_inputs[input_index] = obs_input
        input_index=input_index+1
    return training_inputs

def save_system_inputs(out_file, training_inputs):
    for (key,value) in training_inputs.items():
        out_file.write("%s|%s\n" % (key, json.dumps(value)))


'''
Create random sets of inputs, to be used to create the training set
'''
def choose_observable_faults(system_file, instances, faults):
    system = System.read_system(system_file)
    inputs_and_faults = dict()
    previously_created = set()
    for instance in xrange(instances):
        while True:
            obs_input = generate_random_inputs(system)
            obs_faults = list(random.sample(system.components.keys(), faults))

            obs_key = json.dumps((obs_input,obs_faults))
            while obs_key in previously_created:
                obs_input = generate_random_inputs(system)
                obs_key = json.dumps((obs_input, obs_faults))

            # Check if the observation is abnormal (compare to normal output)
            for comp in obs_faults:
                system.inject_fault(system, comp)
            obs_output = system.propagate(obs_input)

            normal_system = System.read_system(system_file)
            normal_output = normal_system.propagate(obs_input)

            # Only consider this input-and-faults pair if it creates observable abnormal outputs
            if obs_output != normal_output:
                break
            else:
                system = normal_system

        inputs_and_faults[instance] = (obs_input, obs_faults)
    return inputs_and_faults

def save_observable_faults(out_file, inputs_and_faults):
    for (key,value) in inputs_and_faults.items():
        out_file.write("%s|%s\n" % (key, json.dumps(value)))

'''
Create all data needed for runner to run
'''
def __main__():
    system_file = "systems/74181.sys"

    system = System.read_system(system_file)
    index_to_inputs = choose_system_inputs(system, 100)
    out_file = open("inputs.txt", "w")
    save_system_inputs(out_file, index_to_inputs)
    out_file.close()

    for faults in [1, 2, 3]:
        index_to_inputs = choose_observable_faults(system_file, 100, faults)
        output_file_name = "inputs_and_faults-%d.txt" % faults
        out_file = open(output_file_name, "w")
        save_observable_faults(out_file, index_to_inputs)
        out_file.close()

if __name__=="__main__":
    main()