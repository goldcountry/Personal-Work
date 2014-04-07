// $Id: inode.cpp,v 1.3 2014-03-26 18:39:40-07 - - $

#include <cassert>
#include <iostream>

using namespace std;

#include "debug.h"
#include "inode.h"


//inode stuff
int inode::next_inode_nr {0};

inode::inode(inode_t init_type): inode_nr (next_inode_nr++), type (init_type) {
   switch (type) {
      case DIR_INODE:
           contents.dirents = new directory();
           break;
      case FILE_INODE:
           contents.data = new wordvec();
           break;
   }
   DEBUGF ('i', "inode " << inode_nr << ", type = " << type);
}

//
// copy ctor -
//    Make a copy of a given inode.  This should not be used in
//    your program if you can avoid it, since it is expensive.
//    Here, we can leverage operator=.
//
inode::inode (const inode& that) {
   *this = that;
}

//
// operator= -
//    Assignment operator.  Copy an inode.  Make a copy of a
//    given inode.  This should not be used in your program if
//    you can avoid it, since it is expensive.
//
inode& inode::operator= (const inode& that) {
   if (this != &that) {
      inode_nr = that.inode_nr;
      type = that.type;
      contents = that.contents;
   }
   DEBUGF ('i', "inode " << inode_nr << ", type = " << type);
   return *this;
}


//inode accessors
int inode::get_inode_nr() const {
   DEBUGF ('i', "inode = " << inode_nr);
   return inode_nr;
}

int inode::size() const {
   int size {0};
   DEBUGF ('i', "size = " << size);
   return size;
}

const wordvec& inode::readfile() const {
   DEBUGF ('i', *contents.data);
   assert (type == FILE_INODE);
   return *contents.data;
}

string inode::get_name(){
  return name;
}

inode_t inode::get_type(){
  return type;
}

directory* inode::get_dirents(){
  return contents.dirents;
}

//inode manipulators
void inode::add_dirent(string newname, inode *newinode){
  assert (type == DIR_INODE);
  contents.dirents->insert (pair<string, inode *> (newname, newinode));
}

void inode::writefile (const wordvec& words) {
   DEBUGF ('i', words);
   assert (type == FILE_INODE);
}

void inode::remove (const string& filename) {
   DEBUGF ('i', filename);
   assert (type == DIR_INODE);
}

inode& inode::mkdir(const string& dirname){
  inode *new_dir = new inode(DIR_INODE);
  new_dir->name = dirname;

}

inode& inode::mkfile(const string& filename){

}

void inode::set_name(string n){
  name = n;
}


//inode_state stuff
inode_state::inode_state() {
  
  DEBUGF ('i', "root = " << (void*) root << ", cwd = " << (void*) cwd
            << ", prompt = " << prompt);
}

//accessors
inode* inode_state::get_root(){
  return root;
}

inode* inode_state::get_cwd(){
  return cwd;
}

string inode_state::get_prompt(){
  return prompt;
}

string inode_state::get_cwd_names(){
  out << cwd_path << endl;
  return out;
}

//manipulators
void inode_state::push_dir(string dirname){
  cwd_path.push_back(dirname);
}

void inode_state::pop_dir(){
  if(cwd_path.size() > 1){
    cwd_path.pop_back();
  }
}

void inode_state::set_prompt(string& np){
  prompt = np;
}

void inode_state::set_root(inode *newroot){
  root = newroot;
}

ostream& operator<< (ostream& out, const inode_state& state) {
   out << "inode_state: root = " << state.root
       << ", cwd = " << state.cwd;
   return out;
}

