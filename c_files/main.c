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
    if (x == 6) {
        return bar(x+y) + 7;
    }
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
    printf("%d \n", foo(6, 7));
    return 0;
}