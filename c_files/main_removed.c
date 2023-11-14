#include <stdio.h>
#include <math.h>

#define foo_INDEX 0
#define bar_INDEX 1

struct foo_ios
{
  int result;
  int x;
  int y;
};

struct bar_ios
{
  int result;
  int x;
};

union block_call
{
  struct foo_ios foo;
  struct bar_ios bar;
};

void block(int index, union block_call *frame)
{
  switch (index)
  {
    foo_LABEL:
    case foo_INDEX:
    {
      int x = frame->foo.x;
      int y = frame->foo.y;
      frame->bar.x = x;
      goto bar_LABEL;
    }


    bar_LABEL:
    case bar_INDEX:
    {
      int x = frame->bar.x;
      frame->bar.result = 5;
      return;
    }


  }

}



int foo(int x, int y)
{
  union block_call frame;
  frame.foo.x = x;
  frame.foo.y = y;
  block(foo_INDEX, &frame);
  return frame.foo.result;
}



int bar(int x)
{
  union block_call frame;
  frame.bar.x = x;
  block(bar_INDEX, &frame);
  return frame.bar.result;
}



int main()
{
  foo(2, 3);
  return 0;
}


