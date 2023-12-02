#include <stdio.h>
#include <math.h>


int gar(int y) {
    printf("gar\n");
    printf("y+2:%d\n", y+2);
    return y + 2;
}

int bar(int x) {
    printf("bar\n");
    printf("x:%d\n", x);
    while (1) {
        gar(12);
        break;
    }
    return gar(7+x);
}

int foo(int x, int y) {
    printf("foo\n");
    if (x == 2) {
        return bar(x+y) + 7;
    }
    else if (x == 6) {
      return bar(x+y);
    }
    else {
        bar(x+y);
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
    printf("%d \n", foo(2, 7));
    printf("%d \n", foo(6, 7));

    return 0;
}