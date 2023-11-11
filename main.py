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
    def __init__(self, function_definition, index, function_call_struct):
        self.function_definition = function_definition
        self.index = index
        self.index_label = f"{function_definition.decl.name}_INDEX"
        self.call_struct = function_call_struct


class GlobalParameters:
    block_call_struct_name = "frame"
    function_call_struct_return_val_name = "result"
    block_name = "block"


def print_element(elem):
    print(c_generator.CGenerator().visit(elem))


def get_function_call_struct(function):
    name = f'{function.decl.name}_ios'
    return_type = deepcopy(function.decl.type.type)
    return_type.declname = GlobalParameters.function_call_struct_return_val_name
    return_variable = c_ast.Decl(GlobalParameters.function_call_struct_return_val_name, [], [], [], [], return_type, None, None)
    decls = [return_variable]
    if function.decl.type.args is not None:
        decls += function.decl.type.args.params
    struct_type = c_ast.Struct(name, decls)
    struct = c_ast.Decl(None, [], [], [], [], struct_type, None, None)
    return struct


def generate_function_info(function, index):
    function_call_struct = get_function_call_struct(function)
    return FunctionInfo(function, index, function_call_struct)


def identify_involved_functions(ast, func_def_map):
    involved_functions = dict()
    index = 0
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef) and item.body.block_items is not None:
            for block_item in item.body.block_items:
                if isinstance(block_item, c_ast.Return) and isinstance(block_item.expr, c_ast.FuncCall):
                    caller_function_name = item.decl.name
                    called_function_name = block_item.expr.name.name
                    if caller_function_name not in involved_functions:
                        involved_functions[caller_function_name] = generate_function_info(item, index)
                        index += 1
                    if called_function_name not in involved_functions:
                        involved_functions[called_function_name] = generate_function_info(func_def_map[called_function_name], index)
                        index += 1
                    break
    return involved_functions


def get_functions_def_map(ast):
    func_def_map = dict()
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef):
            func_def_map[item.decl.name] = item
    return func_def_map


def generate_block_call_struct(involved_functions):
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


def generate_block_call_struct_instantiation(block_call_struct):
    name = GlobalParameters.block_call_struct_name
    type = deepcopy(block_call_struct.type)
    type.decls = None
    type_declaration = c_ast.TypeDecl(name, [], None, type)
    instance = c_ast.Decl(name, [], [], [], [], type_declaration, None, None)
    return instance


def generate_2d_struct_ref(inner_struct_name, inner_struct_field, outer_struct_field):
    type = "."
    inner_struct_ref = c_ast.StructRef(c_ast.ID(inner_struct_name), type, c_ast.ID(inner_struct_field))
    outer_struct_ref = c_ast.StructRef(inner_struct_ref, type, c_ast.ID(outer_struct_field))
    return outer_struct_ref


def generate_return_stmt(function_name):
    return_expr = generate_2d_struct_ref(GlobalParameters.block_call_struct_name,
                                         function_name,
                                         GlobalParameters.function_call_struct_return_val_name)

    return_stmt = c_ast.Return(return_expr)
    return return_stmt


def generate_block_call_stmt(index_label):
    block_call_struct_name = c_ast.ID(GlobalParameters.block_call_struct_name)
    exprs = [c_ast.ID(index_label), c_ast.UnaryOp("&", block_call_struct_name)]
    args = c_ast.ExprList(exprs)
    block_call_stmt = c_ast.FuncCall(c_ast.ID(GlobalParameters.block_name), args)
    return block_call_stmt


def generate_frame_assignments(block_items, function_info):
    function_args = function_info.function_definition.decl.type.args
    if function_args is None:
        return

    function_name = function_info.function_definition.decl.name
    for param in function_args.params:
        param_name = c_ast.ID(param.name)
        frame_field = generate_2d_struct_ref(GlobalParameters.block_call_struct_name,
                                             function_name,
                                             param.name)
        assignment = c_ast.Assignment('=', frame_field, param_name)
        block_items.append(assignment)


def generate_new_function_definitions(involved_functions, block_call_struct):
    block_call_struct_instance = generate_block_call_struct_instantiation(block_call_struct)
    for function in involved_functions:
        block_items = [block_call_struct_instance]
        generate_frame_assignments(block_items, involved_functions[function])
        block_items.append(generate_block_call_stmt(involved_functions[function].index_label))
        block_items.append(generate_return_stmt(function))

        involved_functions[function].function_definition.body.block_items = block_items


def remove_tail_calls(filename):
    ast = parse_file(filename, use_cpp=False)
    func_def_map = get_functions_def_map(ast)
    involved_functions = identify_involved_functions(ast, func_def_map)
    block_call_struct = generate_block_call_struct(involved_functions)
    generate_new_function_definitions(involved_functions, block_call_struct)
    # print_element(ast)
    pass

if __name__ == "__main__":
    remove_tail_calls(filename="c_files/main.c")
