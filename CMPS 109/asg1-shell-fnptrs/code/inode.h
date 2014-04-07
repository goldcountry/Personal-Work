// $Id: inode.h,v 1.6 2014-03-26 19:55:18-07 - - $

#ifndef __INODE_H__
#define __INODE_H__

#include <exception>
#include <iostream>
#include <map>
#include <vector>

using namespace std;

#include "util.h"

//
// inode_t -
//    An inode is either a directory or a plain file.
//

enum inode_t {DIR_INODE, FILE_INODE};

//
// directory -
//    A directory is a list of paired strings (filenames) and inodes.
//    An inode in a directory may be a directory or a file.
//

class inode;
typedef map<string, inode*> directory;

//
// inode_state -
//    A small convenient class to maintain the state of the simulated
//    process:  the root (/), the current directory (.), and the
//    prompt.
//

class inode_state {
   friend class inode;
   friend ostream& operator<< (ostream& out, const inode_state&);
   private:
      inode_state (const inode_state&) = delete; // copy ctor
      inode_state& operator= (const inode_state&) = delete; // op=
      inode* root {nullptr};
      inode* cwd {nullptr};
      string prompt {"% "};
      wordvec cwd_path;
   public:
      //constructors
      inode_state();

      //accessors
      inode* get_root();
      inode* get_cwd();
      string get_prompt();
      string get_cwd_names();
      
      //manipulators
      void set_prompt(string& np);
      void push_dir(string dirname);
      void pop_dir();
};

ostream& operator<< (ostream& out, const inode_state&);


//
// class inode -
//
// inode ctor -
//    Create a new inode of the given type, using a union.
// get_inode_nr -
//    Retrieves the serial number of the inode.  Inode numbers are
//    allocated in sequence by small integer.
// size -
//    Returns the size of an inode.  For a directory, this is the
//    number of dirents.  For a text file, the number of characters
//    when printed (the sum of the lengths of each word, plus the
//    number of words.
// readfile -
//    Returns a copy of the contents of the wordvec in the file.
//    Throws an yshell_exn for a directory.
// writefile -
//    Replaces the contents of a file with new contents.
//    Throws an yshell_exn for a directory.
// remove -
//    Removes the file or subdirectory from the current inode.
//    Throws an yshell_exn if this is not a directory, the file
//    does not exist, or the subdirectory is not empty.
//    Here empty means the only entries are dot (.) and dotdot (..).
// mkdir -
//    Creates a new directory under the current directory and 
//    immediately adds the directories dot (.) and dotdot (..) to it.
//    Note that the parent (..) of / is / itself.  It is an error
//    if the entry already exists.
// mkfile -
//    Create a new empty text file with the given name.  Error if
//    a dirent with that name exists.
//    




class inode {
   friend class inode_state;
   private:
      int inode_nr;
      inode_t type;
      union {
         directory* dirents;
         wordvec* data;
      } contents;
      static int next_inode_nr;
      string name;
   public:
      //constructors
      inode (inode_t init_type);
      inode (const inode& source);
      inode& operator= (const inode& from);
      
      //accessors
      int get_inode_nr() const;
      int size() const;
      const wordvec& readfile() const;
      string get_name();
      inode_t get_type();
      directory* get_dirents();
      
      //manipulators
      void add_dirent(string newname, inode *newinode);
      void writefile (const wordvec& newdata);
      void remove (const string& filename);
      inode& mkdir (const string& dirname);
      inode& mkfile (const string& filename);
      void set_name(string n);
};

#endif

