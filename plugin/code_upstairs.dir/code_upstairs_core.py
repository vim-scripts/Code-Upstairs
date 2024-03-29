#!/usr/bin/env python
###
# Copyright 2013 Tomasz Wyderka <wyderkat@cofoh.com>
#  www.cofoh.com
# Licensed under GPL-2
##

import os
import fnmatch
from subprocess import Popen,PIPE  
from collections import OrderedDict as OD

def error( txt ):
  print "Error: %s!!!" % txt

class MissingSources(Exception):
  """
  Thrown when cscope or other parser cannot get data from sources.
  Probably file sources are missing
  """
  pass

class MissingScopeApp(Exception):
  """
  Thrown when cscope or pycscope or other parser cannot be started
  """
  pass

def count_file_types( pattern ):
  count = 0
  for root, dirnames, filenames in os.walk('.'):
    for filename in fnmatch.filter(filenames, pattern):
      count += 1
  return count

def init_connection( dir = ".",  mode = None ):
  CSCOPE = 'cscope'

  if mode == None:
    c_count = count_file_types("*.c")
    py_count = count_file_types("*.py")
    if c_count > py_count:
      mode = "c"
    elif py_count > c_count:
      mode = "python"
    else: # equal
      mode = "c"

  if mode == "c":
    special_flags = ['-k','-R' ]
  elif mode == "python":
    code = os.system("pycscope -R")
    if code != 0:
      raise MissingScopeApp("Pycscope cannot be launch")
    # -d not generate db
    special_flags = ['-d']

  try:
    return Popen( [CSCOPE,'-l'] + special_flags,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                cwd=dir )
  except OSError:
    raise MissingScopeApp("Cscope cannot be launch")

def shutdown_connection ( popen ):
  popen.terminate()

def Create_tree( conn, f_name, parent = None, visited = {} ) :
# visited {'fun_name': Function, 'not_our_fun_name': None }
  """
  recursive tree made of Function nodes
  """
  try:
    f = visited[ f_name ]
    if f:
      parent.add_existing_call( f ) 
  except KeyError: # not visited 
    visited[f_name] = None
    definition = writeln(conn, "1"+f_name, None)
    if len(definition) > 0: # it's function in our project
      if parent:
        f = parent.add_new_call( f_name ) 
      else:
        f = Function(f_name)
      visited[f.name] = f
      f.file = definition[0][0]
      if f.file[:2] == "./": # pycscope bug
        f.file = f.file[2:]
      f.line = int(definition[0][2])
      outs = writeln(conn, "2"+f.name)
      for hit in outs:
        Create_tree( conn, hit, f , visited)
      if not parent:
        return f


def writeln( conn, str, columns=1 ):
  """
  write command line to cscope -l 
  and read output from every line and 
  given column. if column== None,
  all columns are returned in sublist
  """
  conn.stdin.write( str + "\n" )
  conn.stdin.flush()
  line = conn.stdout.readline()
  try:
    no_of_lines = int( line.split()[2] ) 
  except IndexError:
    raise MissingSources("No data for %s command" % str)
  #print "NO %d" %no_of_lines
  result = []
  for i in range(no_of_lines):
    line = conn.stdout.readline()
    elements = line.split()
    #print elements[1]
    if columns != None:
      result.append( elements[columns] )
    else:
      result.append( elements )
  return result

def first_the_same_element_in_lists( l1, l2 ):
  """
  find the first common element in two lists
  Return (that element, index in l1, index in l2)
  """
  i1 = 0
  for e1 in l1:
    try:
      i2 = l2.index(e1)
      return (e1, i1, i2)
    except ValueError:
      pass
    i1 += 1
  return (None, None, None)


class Function(object):
  all = {} # non recurisve list of all Functions

  def who( me , fname ): 
    return me.all[ fname ]

  def __init__(me, name):
    me.calls = {} # Functions which are called from 'me' Function 
    me.used  = {} # Functions which are calling 'me' Function
                  # This is also list of parrents
    me.name = name # Function name, duplicated from parents.calls dictionary
    Function.all[ name ] = me
  def add_new_call(me, name):
    """
    add new Function element as a child to this element
    """
    f = Function( name ) 
    me.calls[ name ] = f # tree structure
    f.used[ me.name ] = me # backreference
    return f
  def add_existing_call(me, she):
    """
    add existing function elment under another (this) parent function
    """
    me.calls[ she.name ] = she # tree structure
    she.used[ me.name ] = me # backreference
    return she
  def print_tree(me, layers = False, graph=False, depth=0, parents={}):
    indentation = "    " * depth
    head = ""
    tail = " "
    #if len(me.used) > 1:
    #  tail += str(len(me.used))
    if len(me.distances) == 1 and me.distances[0] == -1:
      pass
    else:
      try:
        tail += str(me.max_distance())
      except ValueError:
        print "ERR %s" % me.name
    if graph:
      tail += str(me.used.keys())
    if layers:
      try:
        tail += "             - %s -" % me.strong_layer
      except AttributeError:
        pass
    print head + indentation + me.name + tail
    if me.name in parents:
      print indentation + "... RECURSION (%s)" % me.name
      return
    else:
      if len(me.calls) == 0:
         #print indentation, "-"
         return
      else:
        parents[ me.name ] = 1 # 1 is just flag
        for fname, f in me.calls.items():
           f.print_tree(layers, graph, depth+1, parents)
        del( parents[ me.name ] )
  def find_strong_layers( me ):
    """
    find layer of functions which have just one and common parent
    """
    Function.strong_layers = {}
    for f in Function.all.values():
      if len(f.used) == 1:
        #print "name %s used %s" % (f.name, f.used.keys()[0] )
        f.strong_layer = f.used.keys()[0]
        try: 
          Function.strong_layers[ f.used.keys()[0] ].append( f )
        except KeyError:
          Function.strong_layers[ f.used.keys()[0] ] = [ ( f ) ]

  def print_strong_layers( me ):
    counter = 0
    for k,v in Function.strong_layers.items():
      for f in v:
        print "%s " % f.name ,
        counter += 1
      print "=> %s" % k 
    print "STRONG RATIO %g" % (float(counter)/len(Function.all))

  def what_strong_layer_childs( me ):
    result = []
    try:
      childs = Function.strong_layers[ me.name ]
    except KeyError:
      return result
    for f in childs:
      result.append( f.name )
    return result

  def what_strong_layer_siblings( me ):
    result = []
    for k,v in Function.strong_layers.items():
      if me in v:
        for f in v:
          if f == me:
            continue
          result.append( f.name )
        break
    return result

  def distances_to_myself ( me, end_name ):
    """ 
    calculate distances to other calls of this function
    """
    me.distances = []
    if me.name in me.used.keys(): # shallow recurence
      me.distances.append( 1 )  # 1 is distance for shallow recurence

    if len(me.used) <= 1:
      me.distances.append( -1 )
    else:
      paths = me.find_all_paths( end_name )
      # every path with each other
      for i in xrange( len( paths ) ):
        for j in xrange( i+1, len( paths ) ):
          (_,d1,d2) = first_the_same_element_in_lists( paths[i][1:], paths[j][1:] )
          me.distances.append( d1 + d2 + 2 )

  def find_all_distances( me, end_name ):
    """
    calculate self distances for every function
    """
    for f in Function.all.values():
      f.distances_to_myself( end_name )

  def max_distance( me ):
    """
    max distance from self-distances
    """
    return max(me.distances)

  def find_all_paths(me,  end_name, path=[]):
    """
    all path from function up to end_name
    end_name usally will be "main"
    """
    path = path + [me.name]
    if me.name == end_name:
        return [path]
    paths = []
    for up_f in me.used.values():
        if up_f.name not in path:
            newpaths = up_f.find_all_paths(end_name, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths
  def get_all_functions_count( me ):
    return len(Function.all)



class Location(object):
  def __init__( me, functions_tree ):
    # building back-reference
    me.backref = {}
    for f in functions_tree.all.values():
      try:
        # table update
        me.backref[ f.file ].append( ( f.line, f.name ) )
      except KeyError:
        # table init
        me.backref[ f.file ] = [ ( f.line, f.name ) ]
    # sorting back-reference
    for i in me.backref.values():
      i.sort( lambda x,y: cmp( x[0],y[0] ) )
    me.ref = functions_tree.all # normal reference
  def what( me, file, line ) :
    """
    What function definition is in this line and file
    """
    founded = None
    try:
      for (l,f) in me.backref[ file ]:
         if l > line :
           break
         founded = f
    except KeyError: # nothing in file
      founded = None
    return founded
  def where( me, function ) :
    """
    Where function is located
    """
    try:
      f = me.ref[ function ] 
      return (f.file, f.line)
    except KeyError:
      return None

class FunctionDB(object):
  """
  Code Upstairs Description of a give function
  """
  def __init__( me, function ):

    me.D = OD () # data, dictionary of functions levels
    # parents
    i = OD()
    for fn in function.used.keys():
      i[ fn ] = 0 # 0 because of later use
    me.D[ "parents" ] = i
    # siblings
    i = OD()
    for fn in function.what_strong_layer_siblings():
      i[ fn ] = 0 # 0 because of later use
    me.D[ "siblings" ] = i
    # childs
    i = OD()
    for fn in function.what_strong_layer_childs():
      i[ fn ] = 0 # 0 because of later use
    me.D[ "childs" ] = i
    # other distances
    for f in function.calls.values():
      d = f.max_distance()
      if d>=0:
        try:
          me.D[ str(d) ][ f.name ] = 0 
        except KeyError:
          me.D[ str(d) ] = OD( [ (f.name, 0) ] )
    # default selection
    me.layer_S = "childs"
    me.fname_S = None
    # list of recently selected functions in layer
    # so we can remember
    me.fnames_S_recent = {}
    # empty list of text layers
    me.T = OD()

  def get_all_layers( me ):
    return me.T.keys() + me.D.keys()

  def get_fnames_in_layer( me , layer):
    try:
      result = me.D[layer].keys()
    except KeyError:
      result = me.T[layer]
    return result

  def prepend_text_layer( me, title, text ):
    me.T[ title ] = text

  def is_text_layer( me, layer ):
    return layer in me.T.keys()

  def get_text_layer( me , layer):
    return me.T[layer]

  def select( me, layer = None, fname = None ):
    if layer:
      me.layer_S = layer
    if fname:
      me.fname_S = fname
    if not me.fname_S:
      try:
        me.fname_S = me.fnames_S_recent[ me.layer_S ]
      except KeyError:
        me.fname_S = None
      if not me.fname_S:
        try:
          me.fname_S = me.get_fnames_in_layer( me.layer_S ) [0]
        except IndexError: # no single fname in layer
          me.fname_S = None

    me.fnames_S_recent[ me.layer_S ] = me.fname_S

  def select_next_layer( me , inc=1 ):
    all = me.get_all_layers()
    idx = all.index( me.layer_S )
    idx = (idx+inc) % len(all)
    me.layer_S = all[idx] 

    me.fname_S = None
    me.select()

  def select_next_fname( me , inc=1 ):
    all_fnames = me.get_fnames_in_layer( me.layer_S )
    if len(all_fnames) == 0:
      return
    if me.fname_S:
      idx = all_fnames.index( me.fname_S )
    else: # me.fname_S == None
      idx = 0
    idx = (idx+inc) % len(all_fnames)
    me.fname_S = all_fnames[idx] 
    me.fnames_S_recent[ me.layer_S ] = me.fname_S

  def is_selected( me, layer = None, fname = None ):
    result = True
    if layer:
      if not me.layer_S == layer:
        result = False
    if fname:
      if not me.fname_S == fname:
        result = False
    return result

  def get_selected( me ):
    return ( me.layer_S, me.fname_S )


if __name__ == "__main__":
  import sys
  fname = "main"
  print "testing from __main__"

  if len(sys.argv) > 1:
    fname = sys.argv[1]

  conn = init_connection()

  root = Create_tree(conn, fname)
  loc = Location( root )
  root.find_strong_layers()
  root.find_all_distances( end_name = fname ) 
  
  root.print_tree(layers=True)
  print "====="
  root.print_strong_layers()
  print "Functions in source %d " % root.get_all_functions_count()
  print "Strong layer for init: %s" % \
      str( root.who("init").what_strong_layer_childs() )
  print "Strong layer siblings for init: %s" % \
      str( root.who("init").what_strong_layer_siblings() )
  #print loc.what( "linenoise.c", 200 )
