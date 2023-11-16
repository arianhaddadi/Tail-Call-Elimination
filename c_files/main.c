#include <stdio.h>
#include <math.h>

int bar(int x);

int gar(int y) {
    printf("y:%d\n", y+2);
    return y + 2;
}

int bar(int x) {
    printf("x:%d\n", x);
    return gar(7+10);
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