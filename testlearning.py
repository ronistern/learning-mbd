import unittest
from systems import System
import generator
from utils import dict_compare
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


if __name__ == '__main__':
    unittest.main()