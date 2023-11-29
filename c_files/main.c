#include <stdio.h>
#include <math.h>


int gar(int y) {
    printf("y:%d\n", y+2);
    return y + 2;
}

int bar(int x) {
    printf("x:%d\n", x);
    return gar(7+x);
}

int foo(int x, int y) {
    printf("foo\n");
    if (x == 2) {
      return bar(x+y);
    }
    for (int i = 0; i < 10; i++) {
        if (i == 5) {
            return bar(10 + 47 * 31);
        }
    }
    return bar(x*y);
}


int main() {
    foo(2, 3);
    foo(3, 3);
    return 0;
}