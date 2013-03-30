Code Upstairs
=============

A plugin for browsing source code at functions level. 

Readability of source code is decreasing when project is getting bigger. The
aim of this plugin is to make code more easily readable and understandable.
In other words it is trying to put big projects more under control.

Normally readability of long single function is preserved by using indentation of
code lines. This plugin provides kind of _indentation_ at higher level -
_indentation_ of whole functions. 

User can see fairly easily how current function is dependent upon others. He
will also get structure of all functions in code in a tree layout if code is clearly
implemented. So therefor _Code Upstairs_ is also kind of quality controller.

Installation
------------
Unpack `cu-vim-VERSION.tgz` and the content of extracted `code_upstairs-VERSION` directory move
to your `~/.vim/`. 

Current version _Code Upstairs_ works only with **C** and **Python**. 
And you need to have installed `cscope` and/or `pycscope`. 

Usage
-----
Open some file of your project and call:

    :CUinit <directory> 

where `<directory>` is the root of your project. 
If skipped current directory will be used.

To turn off _Code Upstairs_ use:

    :CUshutdown


Statusline
----------
Functions structure is shown in statusline.
Because of limited space statusline is divided to layers. 
Following layers are shown in order from left to right:

+ __(-)__ layer showing original vim statusline
+ __(P)__ layer with parents of current function. Parent is a function from
  which current function is called.
+ __(S)__ siblings layer shows functions which are on the same level with
  current function looking from parent perspective (Frankly saying siblings are
  __pure child functions__ of parent function)
+ __(C)__ children layer shows __pure child functions__ of current function.
  __Pure child function__ is a function which is called only from one parent. 
+ __(XX)__ (where `XX` is a number) layer shows children functions in distance
  `XX` from current function. Those are not __pure child
  functions__, they have more than one parent and therefore theirs calls are
  distributed over code. Distance `XX` tells how far they are distributed.
  Further functions distances can mean not clear implementation or code design.


Keybindings
-----------
Default keybindings can be change using variables given in parenthesis. 

+ `<space>.` and `<space>,` will switch layer forward and backward.
  (`CUkeyNextLayer` and `CUkeyPrevLayer`)
+ `<space>m` and `<space>n` will switch function in a layer forward and
  backward. (`CUkeyNextFunction` and `CUkeyPrevFunction`)
+ `<space>b` will jump to function definition (`CUkeyJumpToFunction`)
+ `<space>/` will highlight function name in vim window (`CUkeyHighlightFunction`)





