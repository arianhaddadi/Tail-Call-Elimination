int foo(int x, int y) {
    return 2;
}

int main() {
    goto label1;
    label1:
    printf("here");
    return foo();
}