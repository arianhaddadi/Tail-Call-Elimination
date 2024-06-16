# Tail Call Elimination in C

This project is an implementation of a tail call eliminator. 
It converts a C file with tail calls to a C file with 
similar functionality that does not have any tail calls anymore. 
The logic of the tail calling and tail called functions 
are moved to a new function 
(called **Block function** in this project), 
and all tail calls are converted 
to **goto** statements.

To run this project, simply run

    `python main.py <inputfile>`

The resulting file will be beside the input file with **"_removed"** appened to its name.
An example of an input file with its tail calls removed
is put in the ***c_files*** directory.