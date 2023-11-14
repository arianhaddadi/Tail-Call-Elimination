import utils
import os
from pycparser import parse_file
from block import Block


def remove_tail_calls(filename):
    temp_filename = f"{filename[:-2]}_temp.c"
    directives = utils.remove_and_save_directives(filename, temp_filename)
    ast = parse_file(temp_filename)
    func_def_map = utils.get_functions_def_map(ast)
    involved_functions = utils.identify_involved_functions(ast, func_def_map)
    block_call_union = Block.generate_block_call_union(involved_functions)
    block_function = Block.generate_block_function(involved_functions, func_def_map)
    utils.change_function_definitions(involved_functions, block_call_union)

    utils.write_result_to_disk(directives, involved_functions, block_call_union, block_function, ast, filename)
    os.remove(temp_filename)


if __name__ == "__main__":
    remove_tail_calls(filename="c_files/main.c")
