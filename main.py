from pycparser import parse_file, c_generator


def translate_to_c(filename):
    ast = parse_file(filename, use_cpp=True)
    generator = c_generator.CGenerator()
    print(generator.visit(ast))


if __name__ == "__main__":
    translate_to_c("main.c")
