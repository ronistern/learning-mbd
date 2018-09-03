import types

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
        return 1 - (inputs[0] * inputs[1] * inputs[2] * inputs[3 ] *inputs[4])

    @staticmethod
    def inverter(inputs):
        return 1 - inputs[0]

    @staticmethod
    def or2(inputs):
        return max(inputs)

    @staticmethod
    def or3(inputs):
        return max(inputs)

    @staticmethod
    def or4(inputs):
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
    def nor8(inputs):
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

    @staticmethod
    def __read_component(line):
        parts = line.strip("[],\n.").split(",")
        comp_type = parts[0]
        comp_name = parts[1]
        comp_output = parts[2]
        comp_inputs = parts[3:]
        return Component(comp_name, comp_type, comp_inputs, comp_output)


    '''
       Read a comma-delimited list from a list of lines, starting with a given start line index and a "[" symbol
       and ending with a line that ends with "]."
       '''
    @staticmethod
    def __read_list(lines, start_line):
        my_list = []
        line_no = start_line
        while True:
            line = lines[line_no].strip()
            line_no = line_no + 1
            # Cut leading and ending []. signs
            if line.startswith("["):
                line = line[1:]
            if line.endswith("]."):
                line = line[:-2]
                my_list.extend(line.split(","))
                break
            new_elements = [x for x in line.split(",") if len(x)>0] # Removing the empty element at the end of the line
            my_list.extend(new_elements)
        return (line_no, my_list)

    @staticmethod
    def read_system(in_file_name):
        in_file = open(in_file_name, "r")
        lines = in_file.readlines()
        system_name = lines[0].strip()

        (line_no, system_inputs) = System.__read_list(lines, 1)
        (line_no, system_outputs) = System.__read_list(lines, line_no)

        # Read components
        components = dict()
        for line in lines[line_no:]:
            component = System.__read_component(line)
            components[component.name] = component
        return System(system_name, system_inputs, system_outputs, components)

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


    def add_probes(self,probes):
        self.outputs + probes


def fault(self, inputs):
    output = self.type(inputs)
    return 1-output

def normal(self, inputs):
    return self.type(inputs)

def inject_fault(system, faulty_component):
    comp = system.components[faulty_component]
    comp.compute = types.MethodType(fault, comp)

def inject_faults(system, faulty_components):
    for comp in faulty_components:
        inject_fault(system,comp)

def clear_fault(system, faulty_component):
     comp = system.components[faulty_component]
     comp.compute = types.MethodType(normal, comp)
