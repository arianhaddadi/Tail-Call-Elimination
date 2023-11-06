from pycparser import parse_file, c_generator, c_ast
from copy import deepcopy


class Parameter:
    def __init__(self, type, name):
        self.type = type
        self.name = name


class FunctionSignature:
    def __init__(self, params, return_type):
        self.params = params
        self.returnType = return_type


class FunctionInfo:
    def __init__(self, function_definition, index, call_struct):
        self.function_definition = function_definition
        self.index = index
        self.call_struct = call_struct


def get_call_struct(function):
    name = f'{function.decl.name}_ios'
    return_type = deepcopy(function.decl.type.type)
    return_type.declname = "result"
    return_variable = c_ast.Decl("result", [], [], [], [], return_type, None, None)
    decls = [return_variable]
    if function.decl.type.args is not None:
        decls += function.decl.type.args.params
    struct_type = c_ast.Struct(name, decls)
    struct = c_ast.Decl(None, [], [], [], [], struct_type, None, None)
    return struct


def add_to_involved_functions(function, involved_functions, index):
    call_struct = get_call_struct(function)
    involved_functions[function.decl.name] = FunctionInfo(function, index, call_struct)


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
                        add_to_involved_functions(func_def_map[block_item.expr.name.name], involved_functions, index)
                        index += 1
                    break
    return involved_functions


def get_functions_def_map(ast):
    func_def_map = dict()
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef):
            func_def_map[item.decl.name] = item
    return func_def_map


def get_block_call_struct(involved_functions):
    name = "block_call"
    decls = []
    for function in involved_functions:
        function_call_struct = involved_functions[function].call_struct
        struct_type = c_ast.Struct(function_call_struct.type.name, None)
        type_declaration = c_ast.TypeDecl(f"{function}_call", [], None, struct_type)
        decl = c_ast.Decl(f"{function}_call", [], [], [], [], type_declaration, None, None)
        decls.append(decl)
    struct_type = c_ast.Struct(name, decls)
    struct = c_ast.Decl(None, [], [], [], [], struct_type, None, None)
    return struct

def remove_tail_calls(filename):
    ast = parse_file(filename, use_cpp=False)
    func_def_map = get_functions_def_map(ast)
    involved_functions = identify_involved_functions(ast, func_def_map)
    block_call_struct = get_block_call_struct(involved_functions)
    # print(c_generator.CGenerator().visit(block_call_struct))
    pass


if __name__ == "__main__":
    remove_tail_calls(filename="c_files/main.c")
