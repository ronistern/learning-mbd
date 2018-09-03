
import random
import json
import math
import copy
from systems import System, inject_fault
from learning import learn, diagnose,fully_observed_subsystems
import generator


def run_experiments(system_file, probes_range, training_inputs_file, training_sizes, faults_file,out_file,extra_data):
    # Prepare output
    results = dict()
    extra_data_values = ",".join([str(item) for item in extra_data.values()])

    # Load faults file
    test_inputs_and_faults = generator.load_observable_faults(faults_file)
    abnormal_observations = test_inputs_and_faults.keys()

    # Load training inputs
    training_inputs = generator.load_system_inputs(training_inputs_file)
    all_training_instances = training_inputs.keys()
    random.shuffle(all_training_instances)

    # Sort potential probes
    system = System.read_system(system_file)
    potential_probes = list(system.variables.difference(system.outputs).difference(system.inputs))
    random.shuffle(potential_probes)

    # Add probes to the system
    for num_of_probes in probes_range:
        probes = potential_probes[:num_of_probes-1]
        system_with_probes = System.read_system(system_file)
        system_with_probes.outputs = system_with_probes.outputs + probes

        # Verify that we only probe the non-input variables
        assert len(set(system_with_probes.outputs).intersection(system_with_probes.inputs)) == 0

        required_training_size = sample_complexity(system_with_probes,0.1, 0.1)

        # Partition to train and test
        for training_size in training_sizes:
            training_instances = all_training_instances[:training_size]

            assert(len(training_instances)>0)

            # Get training input/output pairs
            training_set = dict()
            for training_instance in training_instances:
                system_inputs = training_inputs[training_instance]
                system_outputs = system_with_probes.propagate(system_inputs)
                training_set[training_instance]=(system_inputs,system_outputs)

            # Learn partial model
            partial_model = learn(system_with_probes,training_set)

            # For each abnormal observation
            for obs in abnormal_observations:
                (obs_input, faulty_components) = test_inputs_and_faults[obs]
                faulty_components = set(faulty_components)
                faulty_system = copy.deepcopy(system_with_probes)
                for comp in faulty_components:
                    inject_fault(faulty_system, comp)

                # Create a new instance and propagate its values
                obs_output = faulty_system.propagate(obs_input)

                (candidate_faults, exonorated) = diagnose(faulty_system,partial_model,obs_input,obs_output)

                identified_faults = faulty_components.intersection(candidate_faults)
                missed_faults = faulty_components.difference(candidate_faults)
                false_positives = candidate_faults.difference(faulty_components)


                results_key = (system_file, num_of_probes, training_size, obs, len(faulty_components))
                results_value = (len(identified_faults),len(missed_faults),len(exonorated),len(false_positives),required_training_size)

                results[results_key]=results_value
                results_key_str = [str(item) for item in results_key]
                results_value_str = [str(item) for item in results_value]
                output_line = "%s,%s,%s\n" % (",".join(results_key_str),",".join(results_value_str), extra_data_values)
                out_file.write(output_line)
                out_file.flush()
    return results

'''
    Run a single experiment
'''
def run_one_experiment(faulty_system, training_set, abnormal_observation):
    # Learn partial model
    partial_model = learn(faulty_system, training_set)
    (obs_input, obs_output) = abnormal_observation
    return diagnose(faulty_system, partial_model, obs_input, obs_output)



def sample_complexity():
    print "system\t probing\t subsystems\t sub-inputs\t m"
    experiments = 100
    for probing in [1, 2, 4, 8, 16, "Full"]:
        for i in xrange(experiments):
            system = System.read_system("systems/74181.sys")
            if probing=="Full":
                system.add_probes(len(system.variables.difference(system.outputs).difference(system.inputs)))
            else:
                system.add_probes(probing)
            system.add_probes(probing)
            subsystems = fully_observed_subsystems(system)
            num_of_subsystems = len(subsystems)
            max_inputs = max([len(subsystem.inputs) for subsystem in subsystems.values()])

            epsilon = 0.1
            delta = 0.1
            m = sample_complexity(system,epsilon,delta)
            print "%s\t %s\t %s\t %s\t %s" % (system.name, probing, num_of_subsystems, max_inputs, m)

'''
Computes the theoretical number of training instances needed for a given system, epsilon, and delta 
'''
def sample_complexity(system,epsilon,delta):
    subsystems = fully_observed_subsystems(system)
    num_of_subsystems = len(subsystems)
    max_inputs = max([len(subsystem.inputs) for subsystem in subsystems.values()])

    sv = math.pow(2, max_inputs) * num_of_subsystems
    return sv / epsilon * math.log(sv / delta)


def main():
    #system_name = "74181.sys"
    system_name = "c3540.sys"
    system_file = "systems/%s" % system_name
    training_inputs_file = "inputs-%s.txt" % system_name

    probes_range = [1,4,8,16,57]
    #training_sizes = [4,16,64,256,1024]
    training_sizes = [4,16,64,256,1024,2048,4096,8192]

    output_file = "joined_output-%s.csv" % system_name
    out_file = open(output_file, "w")

    headers_written = False

    # Headers
    for faults in [1,2,3]:
        faults_file = "inputs_and_faults-%s-%d.txt" % (system_name,faults)
        for i in xrange(5):
            print "Iteration %d, Faults %d" % (i,faults)

            extra_data =dict()
            extra_data["faults"]=faults
            extra_data["iteration"] = i

            if headers_written==False:
                headers = ["system", "probes", "training", "instance", "faults", \
                           "found_faults", "missed_faults", "exonorated", "false positives", "m"] + extra_data.keys() + [
                              "\n"]
                out_file.write(",".join(headers))
                headers_written=True

            run_experiments(system_file, probes_range, training_inputs_file, training_sizes, faults_file,out_file,extra_data)

    out_file.close()
if __name__=="__main__":
    main()



