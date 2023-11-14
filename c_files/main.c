#include <stdio.h>
#include <math.h>


int foo(int x, int y) {
    return bar(x);
}

int bar(int x) {
    return 5;
}

int main() {
    foo(2, 3);
    return 0;
}