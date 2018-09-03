import unittest
from systems import System,inject_faults
import generator
import utils

'''
Test the generator module
'''
class TestGenerator(unittest.TestCase):
    def test_generate_observable_faults(self):
        system_file = "systems/74181.sys"
        index_to_inputs = generator.choose_observable_faults(system_file, 100, 1)

        for index in index_to_inputs.keys():
            (obs_input, faulty_components) = index_to_inputs[index]
            normal_system = System.read_system(system_file)
            normal_output = normal_system.propagate(obs_input)

            faulty_system = System.read_system(system_file)
            inject_faults(faulty_system,faulty_components)
            abnormal_output = faulty_system.propagate(obs_input)

            (added, removed, modified, same) = utils.dict_compare(normal_output,abnormal_output)
            if len(added)==0 and len(removed)==0 and len(modified)==0:
                self.fail("Added = %d, Removed = %d, Modified = %d" % (len(added), len(removed), len(modified)))
