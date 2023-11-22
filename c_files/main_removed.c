#include <stdio.h>
#include <math.h>

#define bar_INDEX 0
#define gar_INDEX 1
#define foo_INDEX 2

struct bar_ios
{
  int result;
  int x;
};

struct gar_ios
{
  int result;
  int y;
};

struct foo_ios
{
  int result;
  int x;
  int y;
};

union block_call
{
  struct bar_ios bar;
  struct gar_ios gar;
  struct foo_ios foo;
};

void block(int index, union block_call *frame)
{
  switch (index)
  {
    bar_LABEL:
    case bar_INDEX:
    {
      int x = frame->bar.x;
      printf("x:%d\n", x);
      frame->gar.y = 7 + x;
      goto gar_LABEL;
    }


    gar_LABEL:
    case gar_INDEX:
    {
      int y = frame->gar.y;
      printf("y:%d\n", y + 2);
      frame->gar.result = y + 2;
      return;
    }


    foo_LABEL:
    case foo_INDEX:
    {
      int x = frame->foo.x;
      int y = frame->foo.y;
      printf("foo\n");
      if (x == 2)
      {
        frame->bar.x = x + y;
        goto bar_LABEL;
      }
      frame->bar.x = x * y;
      goto bar_LABEL;
    }


  }

}



int bar(int x);
int gar(int y)
{
  union block_call frame;
  frame.gar.y = y;
  block(gar_INDEX, &frame);
  return frame.gar.result;
}

int bar(int x)
{
  union block_call frame;
  frame.bar.x = x;
  block(bar_INDEX, &frame);
  return frame.bar.result;
}

int foo(int x, int y)
{
  union block_call frame;
  frame.foo.x = x;
  frame.foo.y = y;
  block(foo_INDEX, &frame);
  return frame.foo.result;
}

int main()
{
  foo(2, 3);
  foo(3, 3);
  return 0;
}


