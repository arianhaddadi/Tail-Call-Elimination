from pycparser import c_ast, c_generator
from copy import deepcopy


class FunctionInfo:
    """
    A class used to store information about the functions involved in the
    tail call process.
    """

    def __init__(self, function_definition, index, function_call_struct):
        self.function_definition = function_definition
        self.index = index
        self.index_label = f"{function_definition.decl.name}_INDEX"
        self.block_label = f"{function_definition.decl.name}_LABEL"
        self.call_struct = function_call_struct


class GlobalParameters:
    """A class for parametrizing constant names used in tail call elimination"""

    block_call_union_instance_name = "frame"
    block_call_union_name = "block_call"
    function_return_val_name = "result"
    block_name = "block"


def generate_function_call_struct(function):
    """
    Generate the struct that stores the parameters and return value of
    the function.
    For example, if the function's declaration is
        float foo(int x, int y)

    the call struct for this function will be
        struct foo_ios {
            float result;
            int x;
            int y;
        }
    """
    name = f"{function.decl.name}_ios"
    return_type = deepcopy(function.decl.type.type)
    return_type.declname = GlobalParameters.function_return_val_name
    return_variable = c_ast.Decl(
        GlobalParameters.function_return_val_name,
        [],
        [],
        [],
        [],
        return_type,
        None,
        None,
    )
    decls = [return_variable]
    if function.decl.type.args is not None:
        decls += function.decl.type.args.params
    struct_type = c_ast.Struct(name, decls)
    struct = c_ast.Decl(None, [], [], [], [], struct_type, None, None)
    return struct


def generate_function_info(function, index):
    """Generates the instance of FunctionInfo class for the given function."""
    function_call_struct = generate_function_call_struct(function)
    return FunctionInfo(function, index, function_call_struct)


def remove_and_save_directives(filename, temp_filename):
    """
    Removes the directives from the given file as Pycparser does not support
    directives and saves them in a list in order to add them to the final
    result. It also discards commented code.
    """
    directives, new_file = [], []
    is_comment = False
    with open(filename) as file:
        for line in file:
            if line.strip():
                if is_comment:
                    if line.strip()[0:2] == "*/":
                        is_comment = False
                    continue
                if line.strip()[0] == "/":
                    if line.strip()[1] == "*":
                        is_comment = (
                            True if line.strip()[-2:] != "*/" else False
                        )
                    continue
                if line.strip()[0] == "#":
                    directives.append(line)
                else:
                    new_file.append(line)

    with open(temp_filename, "w") as file:
        file.writelines(new_file)

    return directives


def get_functions_def_map(ast):
    """
    Generate a mapping from the name of the function to its FuncDef.
    FuncDef instance is created by Pycparser when the source code is parsed
    into an AST.
    """
    func_def_map = dict()
    for item in ast.ext:
        if isinstance(item, c_ast.FuncDef):
            func_def_map[item.decl.name] = item
    return func_def_map


def identify_involved_functions(ast, func_def_map):
    """
    Identify the functions that either tail call another function or are
    tail called by another function in order to add them to the block function.
    """
    involved_functions = dict()
    index = 0
    for item in ast.ext:
        if (
            isinstance(item, c_ast.FuncDef)
            and item.body.block_items is not None
        ):
            for block_item in item.body.block_items:
                if isinstance(block_item, c_ast.Return) and isinstance(
                    block_item.expr, c_ast.FuncCall
                ):
                    caller_function_name = item.decl.name
                    called_function_name = block_item.expr.name.name
                    if caller_function_name not in involved_functions:
                        involved_functions[caller_function_name] = (
                            generate_function_info(item, index)
                        )
                        index += 1
                    if called_function_name not in involved_functions:
                        involved_functions[called_function_name] = (
                            generate_function_info(
                                func_def_map[called_function_name], index
                            )
                        )
                        index += 1
                    break
    return involved_functions


def write_result_to_disk(
    directives,
    involved_functions,
    block_call_union,
    block_function,
    ast,
    filename,
):
    """Write the final result of the tail call elimination process to disk."""
    file_content = ""
    visitor = c_generator.CGenerator()

    for directive in directives:
        file_content += directive

    file_content += "\n"
    for function in involved_functions:
        function_info = involved_functions[function]
        file_content += (
            f"""#define {function_info.index_label} {function_info.index}\n"""
        )

    file_content += "\n"
    for function in involved_functions:
        file_content += (
            "extern "
            + visitor.visit(
                involved_functions[function].function_definition.decl
            )
            + ";\n"
        )

    for function in involved_functions:
        file_content += (
            "\n"
            + visitor.visit(involved_functions[function].call_struct)
            + ";\n"
        )

    file_content += "\n" + visitor.visit(block_call_union) + ";\n"
    file_content += "\n" + visitor.visit(block_function) + "\n"
    file_content += "\n" + visitor.visit(ast) + "\n"

    with open(f"{filename[:-2]}_removed.c", "w") as file:
        file.write(file_content)


def generate_2d_struct_ref(
    inner_struct_name,
    inner_struct_field,
    outer_struct_field,
    inner_ptr=False,
    outer_ptr=False,
):
    """
    Generates a 2d struct ref.
    2d struct ref is like foo.bar.gar
    inner_ptr and outer_ptr mean that instead of ., it must be ->
    like foo.bar->gar or foo->bar.get depending on whether it's inner or
    outer ptr.
    """
    inner_ref_operator = "." if inner_ptr is False else "->"
    outer_ref_operator = "." if outer_ptr is False else "->"
    inner_struct_ref = c_ast.StructRef(
        c_ast.ID(inner_struct_name),
        inner_ref_operator,
        c_ast.ID(inner_struct_field),
    )
    outer_struct_ref = c_ast.StructRef(
        inner_struct_ref, outer_ref_operator, c_ast.ID(outer_struct_field)
    )
    return outer_struct_ref
