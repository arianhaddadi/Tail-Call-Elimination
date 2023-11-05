from pycparser import parse_file, c_generator, c_ast


class Parameter:
    def __init__(self, type, name):
        self.type = type
        self.name = name


class FunctionSignature:
    def __init__(self, params, return_type):
        self.params = params
        self.returnType = return_type


class FunctionInfo:
    def __init__(self, function_definition, index, input_output_struct):
        self.function_definition = function_definition
        self.index = index
        self.input_output_struct = input_output_struct


def get_input_output_struct(function):
    struct = c_ast.Struct()


def add_to_involved_functions(function, involved_functions, index):
    input_output_struct = get_input_output_struct(function)
    involved_functions[function.decl.name] = FunctionInfo(function, index, input_output_struct)
    pass


def identify_involved_functions(ast, func_def_map):
    involved_functions = dict()
    index = 0
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef) and item.body.block_items is not None:
            for block_item in item.body.block_items:
                if isinstance(block_item, c_ast.Return) and isinstance(block_item.expr, c_ast.FuncCall):
                    if item.decl.name not in involved_functions:
                        add_to_involved_functions(item, involved_functions, index)
                        index += 1
                    if block_item.expr.name not in involved_functions:
                        add_to_involved_functions(func_def_map[block_item.expr.name], involved_functions, index)
                        index += 1
                    break
    return involved_functions


def get_functions_def_map(ast):
    func_def_map = dict()
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef):
            func_def_map[item.decl.name] = item
    return func_def_map


def remove_tail_calls(filename):
    ast = parse_file(filename, use_cpp=False)
    func_def_map = get_functions_def_map(ast)
    involved_functions = identify_involved_functions(ast, func_def_map)
    pass


if __name__ == "__main__":
    remove_tail_calls(filename="c_files/main.c")
