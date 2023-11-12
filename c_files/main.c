int foo(int x, int y) {
    return bar(x);
}

int bar(int x) {
    return 5;
}


void block(int index, union block_call *frame) {
    switch (index) {
        foo_LABEL:
        case (foo_INDEX): {
            int x = frame->foo.x;
            int y = frame->foo.y;
            frame->bar.x = x;
            goto bar_LABEL;
        }

        bar_LABEL:
        case (bar_INDEX): {
            int x = frame->bar.x;
            frame->bar.result = 5;
            return;
        }
    }
}

int main() {
    foo(2, 3);
    return 0;
}