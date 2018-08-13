import ast
import random

from systems import Subsystem

'''
    Learning for full probing
'''
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
def diagnose(faulty_system, partial_model, obs_input, obs_output):
    # Learn from the training set
    (output_to_subsystem, subsystem_to_behavior) = partial_model

    # Diagnose
    (surely_faulty, normally_behaving) = identify_surely_normal_inputs(subsystem_to_behavior, obs_input,obs_output)

    candidate_faults = set()
    exonorated = set()
    for component in faulty_system.components.values():
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
