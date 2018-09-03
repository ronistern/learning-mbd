import unittest
from systems import System
from utils import dict_compare
import runner
import systems
import generator

class TestExperiment(unittest.TestCase):

    '''
    Test saving and loading generated system inputs
    '''
    def test_save_and_load_inputs(self):
        system = System.read_system("systems/74181.sys")
        index_to_inputs = generator.choose_system_inputs(system, 100)

        out_file = open("inputs.txt", "w")
        generator.save_system_inputs(out_file, index_to_inputs)
        out_file.close()
        loaded_index_to_inputs = generator.load_system_inputs("inputs.txt")

        self.assertEqual(len(index_to_inputs),len(loaded_index_to_inputs))
        for key in index_to_inputs.keys():
            self.assertTrue(loaded_index_to_inputs.has_key(key))
            inputs = index_to_inputs[key]
            loaded_inputs = loaded_index_to_inputs[key]
            (added, removed, modified, same) = dict_compare(inputs,loaded_inputs)
            self.assertTrue(len(added)==0)
            self.assertTrue(len(removed) == 0)
            self.assertTrue(len(modified) == 0)


    '''
    Test saving and loading generated system inputs
    '''
    def test_save_and_load_inputs_and_faults(self):
        for faults in [1,2,3]:
            system_file = "systems/74181.sys"
            index_to_inputs = generator.choose_observable_faults(system_file, 100, faults)

            output_file_name = "inputs_and_faults-%d.txt" % faults

            out_file = open(output_file_name, "w")
            generator.save_observable_faults(out_file, index_to_inputs)
            out_file.close()

            loaded_index_to_inputs = generator.load_observable_faults(output_file_name)

            self.assertEqual(len(index_to_inputs),len(loaded_index_to_inputs))
            for key in index_to_inputs.keys():
                self.assertTrue(loaded_index_to_inputs.has_key(key))
                (inputs,faults) = index_to_inputs[key]
                (loaded_inputs, loaded_faults) = loaded_index_to_inputs[key]
                (added, removed, modified, same) = dict_compare(inputs,loaded_inputs)
                self.assertTrue(len(added)==0)
                self.assertTrue(len(removed) == 0)
                self.assertTrue(len(modified) == 0)

                self.assertEqual(set(faults), set(loaded_faults))


    ''' A helper funciton that creates an inputs file all the possible inputs for a given system '''
    def __create_full_training_set(self):
        system_file = "systems/74181.sys"
        training_inputs_file = "test_inputs.txt"

        system = System.read_system(system_file)
        training_set = generator.choose_system_inputs(system, 16384)
        out_file = open(training_inputs_file, "w")
        generator.save_system_inputs(out_file, training_set)
        out_file.close()

    # ''' Check that if we observed all inputs and we have full probing then we will never miss a fault'''
    def test_full_probing(self):
        system_file = "systems/74181.sys"
        probes_range = [57]
        training_inputs_file="test_inputs.txt"

        training_sizes = [16384]
        faults = 1
        faults_file = "inputs_and_faults-%d.txt" % faults
        extra_data =dict()
        output_file = "test_output.csv"
        out_file = open(output_file, "w")
        results=runner.run_experiments(system_file, probes_range, training_inputs_file, training_sizes, faults_file,out_file,extra_data)
        out_file.close()

        for (key,value) in results.items():
            (identified_faults, missed, exonerated, fault_positives, m) = value
            (system_file, num_of_probes, training_size, abnormal_obs, faults) = key
            if missed!=0:
                print abnormal_obs
            self.assertEqual(missed,0)

    def test_focused(self):
        # Create training set
        # self.__create_full_training_set()

        # Load training inputs
        training_inputs_file="test_inputs.txt"
        training_inputs = generator.load_system_inputs(training_inputs_file)
        training_instances = training_inputs.keys()

        # Sort potential probes
        system = System.read_system("systems/74181.sys")
        potential_probes = list(system.variables.difference(system.outputs).difference(system.inputs))
        system.add_probes(potential_probes)

        # Get training input/output pairs
        training_set = dict()
        for training_instance in training_instances:
            system_inputs = training_inputs[training_instance]
            system_outputs = system.propagate(system_inputs)
            training_set[training_instance] = (system_inputs, system_outputs)

        # Load faults file
        test_inputs_and_faults = generator.load_observable_faults("inputs_and_faults-1.txt")
        (obs_input, faulty_components) = test_inputs_and_faults[89]
        faulty_components = set(faulty_components)

        # Create an abnormal observation
        systems.inject_faults(system, faulty_components)
        obs_output = system.propagate(obs_input)

        (candidate_faults, exonorated) = runner.run_one_experiment(system, training_set,(obs_input,obs_output))
        missed_faults = faulty_components.difference(candidate_faults)

        self.assertEqual(len(missed_faults),0)



if __name__ == '__main__':
    unittest.main()