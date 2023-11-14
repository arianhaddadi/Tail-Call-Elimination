#include <stdio.h>
#include <math.h>

int bar(int x) {
    printf("x:%d\n", x);
    return 5 + 2;
}

int foo(int x, int y) {
    printf("foo\n");
    if (x == 2) {
      return bar(x+y);
    }
    return bar(x*y);
}


int main() {
    foo(2, 3);
    return 0;
}