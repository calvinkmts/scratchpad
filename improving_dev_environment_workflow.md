# Improving Dev Environment Workflow

## Problem

So, every morning I have to open up my terminal (using the Windows Terminal because I mainly develop on Windows), type ls, hit cd Workspace, and then type again until I get to the directory I want and then lastly type `code .` to open up my vs code. 

Now it may be not only just the morning, because I sometimes need to switch back between multiple projects which means, opening another terminal and then cd-ing until I find the directory I want and then opening up another `code .`. 

## Key points 

I already know what are the projects names are, and everything is in one place, so I want to can fuzzy find (using the fzf) program, and then click one of the results and cd to to it and then open it. 

## Requirements

There is two experience I want from this small scripts, 

1. I can just select from the list of fzf, and hit enter on one and cd to it.
2. I can also pipe another program from the result to open say like a text editor (in this case VSCode or nvim)

For this script to exists, I want it to be able 

1. Easily modifable, meaning it need to exists inside a git environment. 
2. I can easily put it on my PATH, without obstructing another directory used by other software on the machine.

## Constraints

This is mainly for a unix-based system. So the main machine I tested on will be debian based. 

1. My personal machine with Pop OS
2. Ubuntu running on WSL 2

