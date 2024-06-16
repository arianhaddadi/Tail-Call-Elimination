#include <stdio.h>
#include <math.h>

#define bar_INDEX 0
#define gar_INDEX 1
#define foo_INDEX 2

extern int bar(int x);
extern int gar(int y);
extern int foo(int x, int y);

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
      printf("bar\n");
      printf("x:%d\n", x);
      while (1)
      {
        frame->gar.y = 12;
        goto gar_LABEL;
        break;
      }

      frame->gar.y = 7 + x;
      goto gar_LABEL;
    }


    gar_LABEL:
    case gar_INDEX:
    {
      int y = frame->gar.y;
      printf("gar\n");
      printf("y+2:%d\n", y + 2);
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
        frame->foo.result = 10;
        return;
      }
      else
        if (x == 6)
      {
        frame->bar.x = x + y;
        goto bar_LABEL;
      }
      else
      {
        frame->bar.x = x / x;
        goto bar_LABEL;
      }
      for (int i = 0; i < 10; i++)
      {
        if (i == 5)
        {
          frame->bar.x = 10 + (47 * 31);
          goto bar_LABEL;
        }
      }

      frame->bar.x = x * y;
      goto bar_LABEL;
    }


  }

}



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
  printf("%d \n", foo(6, 7));
  printf("%d \n", foo(2, 7));
  printf("%d \n", foo(8, 7));
  return 0;
}


