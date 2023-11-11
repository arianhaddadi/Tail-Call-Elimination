int foo(int x, int y) {
    return 2;
}
struct sqq {
    int y;
};
struct ss {
    struct sqq sqaz;
};
int main() {
    goto label1;
    label1:
    printf("here");
    return foo();
}