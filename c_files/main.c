int foo() {}

int main() {
    goto label1;
    label1:
    printf("here");
    return foo();
}