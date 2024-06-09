from src import utils
import os
from pycparser import parse_file
from src.block import Block
from src.new_functions import NewFunctions
import sys


def remove_tail_calls(filename):
    """Calls all the functions for the steps of the tail call elimination process."""
    temp_filename = f"{filename[:-2]}_temp.c"
    directives = utils.remove_and_save_directives(filename, temp_filename)

    ast = parse_file(temp_filename)
    func_def_map = utils.get_functions_def_map(ast)
    involved_functions = utils.identify_involved_functions(ast, func_def_map)
    block_call_union = Block.generate_block_call_union(involved_functions)
    block_function = Block.generate_block_function(involved_functions, func_def_map)
    NewFunctions.change_function_definitions(involved_functions, block_call_union)

    utils.write_result_to_disk(directives, involved_functions, block_call_union, block_function, ast, filename)
    os.remove(temp_filename)


if __name__ == "__main__":
    filename = "../c_files/main.c"
    if len(sys.argv) > 1 and sys.argv[1]:
        filename = sys.argv[1]
    remove_tail_calls(filename=filename)
