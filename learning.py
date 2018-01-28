import ast
import random

class Component(object):


    @staticmethod
    def buffer(inputs):
        return inputs[0]

    @staticmethod
    def and2(inputs):
        return inputs[0] * inputs[1]

    @staticmethod
    def and3(inputs):
        return inputs[0] * inputs[1] * inputs[2]

    @staticmethod
    def and4(inputs):
        return inputs[0] * inputs[1] * inputs[2] * inputs[3]

    @staticmethod
    def and5(inputs):
        return inputs[0] * inputs[1] * inputs[2] * inputs[3] * inputs[4]

    @staticmethod
    def nand2(inputs):
        return 1 - inputs[0] * inputs[1]

    @staticmethod
    def nand3(inputs):
        return 1 - (inputs[0] * inputs[1] * inputs[2])

    @staticmethod
    def nand4(inputs):
        return 1 - (inputs[0] * inputs[1] * inputs[2] * inputs[3])

    @staticmethod
    def nand5(inputs):
        return 1 - (inputs[0] * inputs[1] * inputs[2] * inputs[3]*inputs[4])

    @staticmethod
    def inverter(inputs):
        return 1 - inputs[0]

    @staticmethod
    def or2(inputs):
        return max(inputs)

    @staticmethod
    def nor2(inputs):
        return 1 - max(inputs)

    @staticmethod
    def nor3(inputs):
        return 1 - max(inputs)

    @staticmethod
    def nor4(inputs):
        return 1 - max(inputs)

    @staticmethod
    def nor5(inputs):
        return 1 - max(inputs)

    @staticmethod
    def xor2(inputs):
        if inputs[0] == inputs[1]:
            return 0
        else:
            return 1

    def __init__(self, comp_name, comp_type, comp_inputs, comp_output):
        self.name = comp_name
        self.type = getattr(self, comp_type)
        self.inputs = comp_inputs
        self.output = comp_output

    def __str__(self):
        return "%s (%s)" % (self.name, self.type)

    def compute(self, inputs):
        return self.type(inputs)


def read_component(line):
    parts = line.strip("[],\n.").split(",")
    comp_type = parts[0]
    comp_name = parts[1]
    comp_output = parts[2]
    comp_inputs = parts[3:]
    return Component(comp_name, comp_type, comp_inputs, comp_output)


class Subsystem:
    def __init__(self, components, comp_inputs, comp_output):
        self.components = components
        self.inputs = comp_inputs
        self.output = comp_output

    def __str__(self):
        return "Subsytem:[%s]" % [comp.name for comp in self.components]


class System:
    @staticmethod
    def __can_compute(computed_vars, component):
        return computed_vars.issuperset(set(component.inputs))

    def __init__(self, name, inputs, outputs, components):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.components = components

        self.variables = set()
        self.variables.update(self.inputs)
        self.variables.update(self.outputs)
        for component in components.values():
            self.variables.update(component.inputs)
            self.variables.add(component.output)

    def propagate(self, input_to_value):
        var_to_value = dict()
        # Initialize the system inputs' values
        for var in self.inputs:
            var_to_value[var] = input_to_value[var]

        not_computed_comps = set(self.components.values())
        computed_comps = set()
        computed_vars = set(var_to_value.keys())

        while len(not_computed_comps) > 0:
            for component in not_computed_comps:
                # Try to compute the component
                if System.__can_compute(computed_vars, component):
                    input_values = [var_to_value[comp_input] for comp_input in component.inputs]
                    output_value = component.compute(input_values)

                    var_to_value[component.output] = output_value
                    computed_vars.add(component.output)
                    computed_comps.add(component)

            not_computed_comps = not_computed_comps.difference(computed_comps)

        # Return the system outputs
        return {sys_output: var_to_value[sys_output] for sys_output in self.outputs}

    def to_print(self):
        print self.name
        print self.inputs
        print self.outputs
        for component_name in self.components.keys():
            print self.components[component_name]
        for comp_input in self.comp_input_to_comps.keys():
            print "%s->%s" % (comp_input, self.comp_input_to_comps[comp_input])


def read_system(in_file_name):
    in_file = open(in_file_name, "r")
    lines = in_file.readlines()
    system_name = lines[0].strip()
    system_inputs = lines[1].strip()[1:-2].split(",")
    system_outputs = lines[2].strip()[1:-2].split(",")

    # Read components
    components = dict()
    for line in lines[3:]:
        component = read_component(line)
        components[component.name] = component
    return System(system_name, system_inputs, system_outputs, components)

## Learning for full probing
def fully_observed_subsystems(system):
    # Map output to the component that generated it
    output_to_comp = dict()
    for component in system.components.values():
        output_to_comp[component.output] = component

    # Store only the components whose outputs are system output
    subsystems = dict()
    for sys_output in system.outputs:
        # Get fully observable subsystem
        component = output_to_comp[sys_output]
        subsystem_components = set([component.name])
        potential_subsystem_inputs = set(component.inputs)
        subsystem_inputs = set()
        while len(potential_subsystem_inputs)>0:
            potential_input = potential_subsystem_inputs.pop()
            if potential_input  in system.outputs or potential_input  in system.inputs:
                subsystem_inputs.add(potential_input)
            else: # The potential input is unobserved, so propagate backwards
                component = output_to_comp[potential_input]
                subsystem_components.add(component.name)

                new_inputs = set(component.inputs).difference(subsystem_inputs)
                potential_subsystem_inputs.update(new_inputs)

        new_subsystem = Subsystem(subsystem_components,subsystem_inputs,sys_output)
        subsystems[sys_output]=new_subsystem
    return subsystems



## Learning for full probing
def learn(system, training_set):
    output_to_comp = dict()
    for component in system.components.values():
        output_to_comp[component.output] = component

    output_to_subsystem = fully_observed_subsystems(system)

    subsystem_to_behavior = dict()
    for instance in training_set.values():
        # Merge inputs and outputs
        observables = instance[0].copy()
        observables.update(instance[1])

        for sys_output in instance[1].keys():
            subsystem = output_to_subsystem[sys_output]
            # Full probing assumption: inputs are also observable
            output_value = observables[sys_output]
            input_values = {comp_input: observables[comp_input] for comp_input in subsystem.inputs}
            if subsystem_to_behavior.has_key(subsystem) == False:
                comp_behavior = dict()
            else:
                comp_behavior = subsystem_to_behavior[subsystem]

            comp_behavior[str(input_values)] = output_value

            subsystem_to_behavior[subsystem] = comp_behavior
    return (output_to_subsystem, subsystem_to_behavior)




# Diagnose
def identify_surely_normal_inputs(subsystem_to_behavior, obs_input, obs_output):
    var_to_value = obs_input.copy()
    var_to_value.update(obs_output)
    observed_vars = set(var_to_value.keys())

    # Identify surely faulty and normally behaving subsystems
    surely_faulty = set()
    normally_behaving = set()
    for subsystem in subsystem_to_behavior.keys():
        if observed_vars.issuperset(subsystem.inputs):
            behavior = subsystem_to_behavior[subsystem]
            comp_inputs = {var: var_to_value[var] for var in subsystem.inputs}
            key = str(comp_inputs)
            if behavior.has_key(key):
                expected_output = behavior[key]
                if var_to_value[subsystem.output] != expected_output:
                    surely_faulty.add(subsystem)
                else:
                    normally_behaving.add(subsystem)
    return  (surely_faulty,normally_behaving)

# Diagnose
def diagnose(system, training_set, obs_input, obs_output):
    # Learn from the training set
    (output_to_subsystem, subsystem_to_behavior) = learn(system,training_set)

    # Diagnose
    (surely_faulty, normally_behaving) = identify_surely_normal_inputs(subsystem_to_behavior, obs_input,obs_output)

    candidate_faults = set()
    exonorated = set()
    for component in system.components.values():
        can_exonorate = True
        for subsystem in output_to_subsystem.values():
            if component.name in subsystem.components:
                if subsystem in surely_faulty:
                    candidate_faults.add(component.name)
                    can_exonorate = False
                    break # Even if in surely normal, this does not exonorate it
                elif subsystem not in normally_behaving:
                    can_exonorate = False

        # If all the subsystems that contain this component are normally behaving, we can exonorate it (from being in a minimal diagnosis)
        if can_exonorate:
            exonorated.add(component.name)

    return (candidate_faults,exonorated)

