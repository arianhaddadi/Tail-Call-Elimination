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
    def __init__(self, function_definition, index, function_call_struct, called_function_name):
        self.function_definition = function_definition
        self.index = index
        self.index_label = f"{function_definition.decl.name}_INDEX"
        self.block_label = f"{function_definition.decl.name}_LABEL"
        self.call_struct = function_call_struct
        self.called_function_name = called_function_name  # TODO: Remove this if unnecessary


class GlobalParameters:
    block_call_union_instance_name = "frame"
    block_call_union_name = "block_call"
    function_return_val_name = "result"
    block_name = "block"


def print_element(elem):
    print(c_generator.CGenerator().visit(elem))


def get_function_call_struct(function):
    name = f'{function.decl.name}_ios'
    return_type = deepcopy(function.decl.type.type)
    return_type.declname = GlobalParameters.function_return_val_name
    return_variable = c_ast.Decl(GlobalParameters.function_return_val_name, [], [], [], [], return_type, None, None)
    decls = [return_variable]
    if function.decl.type.args is not None:
        decls += function.decl.type.args.params
    struct_type = c_ast.Struct(name, decls)
    struct = c_ast.Decl(None, [], [], [], [], struct_type, None, None)
    return struct


def generate_function_info(function, index, called_function_name=None):
    function_call_struct = get_function_call_struct(function)
    return FunctionInfo(function, index, function_call_struct, called_function_name)


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
                        involved_functions[caller_function_name] = generate_function_info(item, index, called_function_name)
                        index += 1
                    else:
                        involved_functions[caller_function_name].called_function_name = called_function_name
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


def generate_block_call_union(involved_functions):
    name = GlobalParameters.block_call_union_name
    decls = []
    for function in involved_functions:
        function_call_struct = involved_functions[function].call_struct
        struct_type = c_ast.Struct(function_call_struct.type.name, None)
        type_declaration = c_ast.TypeDecl(f"{function}_call", [], None, struct_type)
        decl = c_ast.Decl(f"{function}_call", [], [], [], [], type_declaration, None, None)
        decls.append(decl)
    union_type = c_ast.Union(name, decls)
    union = c_ast.Decl(None, [], [], [], [], union_type, None, None)
    return union


def generate_block_call_struct_instantiation(block_call_union):
    name = GlobalParameters.block_call_union_instance_name
    type = deepcopy(block_call_union.type)
    type.decls = None
    type_declaration = c_ast.TypeDecl(name, [], None, type)
    instance = c_ast.Decl(name, [], [], [], [], type_declaration, None, None)
    return instance


def generate_2d_struct_ref(inner_struct_name, inner_struct_field, outer_struct_field):
    ref_operator = "."
    inner_struct_ref = c_ast.StructRef(c_ast.ID(inner_struct_name), ref_operator, c_ast.ID(inner_struct_field))
    outer_struct_ref = c_ast.StructRef(inner_struct_ref, ref_operator, c_ast.ID(outer_struct_field))
    return outer_struct_ref


def generate_return_stmt(function_name):
    return_expr = generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                         function_name,
                                         GlobalParameters.function_return_val_name)

    return_stmt = c_ast.Return(return_expr)
    return return_stmt


def generate_block_call_stmt(index_label):
    block_call_struct_name = c_ast.ID(GlobalParameters.block_call_union_instance_name)
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
        frame_field = generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                             function_name,
                                             param.name)
        assignment = c_ast.Assignment('=', frame_field, param_name)
        block_items.append(assignment)


def change_function_definitions(involved_functions, block_call_union):
    block_call_struct_instance = generate_block_call_struct_instantiation(block_call_union)
    for function in involved_functions:
        block_items = [block_call_struct_instance]
        generate_frame_assignments(block_items, involved_functions[function])
        block_items.append(generate_block_call_stmt(involved_functions[function].index_label))
        block_items.append(generate_return_stmt(function))

        involved_functions[function].function_definition.body.block_items = block_items


def remove_and_save_directives(filename):
    directives, new_file = [], []
    with open(filename) as file:
        for line in file:
            if line.strip():
                if line.strip()[0] == '#':
                    directives.append(line)
                else:
                    new_file.append(line)

    with open(filename, "w") as file:
        file.writelines(new_file)

    return directives


def generate_block_function_index_arg_declaration():
    declaration_type = c_ast.TypeDecl("index", [], [], c_ast.IdentifierType(['int']))
    declaration = c_ast.Decl('index', [], [], [], [], declaration_type, None, None)
    return declaration


def generate_block_function_block_call_arg_declaration():
    pointer_union_type = c_ast.Union(GlobalParameters.block_call_union_name, None)
    pointer_type = c_ast.TypeDecl(GlobalParameters.block_call_union_instance_name, [], None, pointer_union_type)
    declaration_type = c_ast.PtrDecl([], pointer_type)
    declaration = c_ast.Decl(GlobalParameters.block_call_union_instance_name, [], [], [], [], declaration_type, None, None)
    return declaration


def generate_block_function_declaration():
    return_type = c_ast.TypeDecl(GlobalParameters.block_name, [], None, c_ast.IdentifierType(["void"]))
    args = c_ast.ParamList([generate_block_function_index_arg_declaration(), generate_block_function_block_call_arg_declaration()])
    declaration_type = c_ast.FuncDecl(args, return_type)
    function_declaration = c_ast.Decl(GlobalParameters.block_name, [], [], [], [], declaration_type, None, None)
    return function_declaration


def generate_function_body_in_block(function_info, func_def_map):
    case_body = None  # TODO: Complete This
    case_stmt = c_ast.Case(c_ast.ID(function_info.index_label), c_ast.Compound(case_body))
    label = c_ast.Label(function_info.block_label, case_stmt)
    return label


def generate_block_function_body(involved_functions, func_def_map):
    functions_bodies = [generate_function_body_in_block(involved_functions[function], func_def_map) for function in involved_functions]
    switch_body = c_ast.Compound(functions_bodies)
    switch_stmt = c_ast.Switch(c_ast.ID('index'), switch_body)
    body_items = [switch_stmt]
    body = c_ast.Compound(body_items)
    return body


def generate_block_function(involved_functions, block_call_union, func_def_map):
    function_declaration = generate_block_function_declaration()
    function_body = generate_block_function_body(involved_functions, func_def_map)
    block_function = c_ast.FuncDef(function_declaration, None, function_body)
    return block_function


def remove_tail_calls(filename):
    # directives = remove_and_save_directives(filename)
    ast = parse_file(filename, use_cpp=False)
    func_def_map = get_functions_def_map(ast)
    involved_functions = identify_involved_functions(ast, func_def_map)
    block_call_union = generate_block_call_union(involved_functions)
    block_function = generate_block_function(involved_functions, block_call_union, func_def_map)
    change_function_definitions(involved_functions, block_call_union)
    print_element(ast)
    pass


if __name__ == "__main__":
    remove_tail_calls(filename="c_files/main.c")
