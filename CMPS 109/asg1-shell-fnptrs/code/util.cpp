// $Id: util.cpp,v 1.8 2014-03-26 18:39:40-07 - - $

#include <cstdlib>
#include <unistd.h>

using namespace std;

#include "util.h"
#include "debug.h"

yshell_exn::yshell_exn (const string& what): runtime_error (what) {
}

int exit_status::status = EXIT_SUCCESS;
static string execname_string;

void exit_status::set (int new_status) {
   status = new_status;
}

int exit_status::get() {
   return status;
}

void setexecname (const string& name) {
   execname_string =  name.substr (name.rfind ('/') + 1);
   DEBUGF ('u', execname_string);
}

string& execname() {
   return execname_string;
}

bool want_echo() {
   const int CIN_FD {0};
   const int COUT_FD {1};
   bool cin_isatty = isatty (CIN_FD);
   bool cout_isatty = isatty (COUT_FD);
   DEBUGF ('u', "cin_isatty = " << cin_isatty
          << ", cout_isatty = " << cout_isatty);
   return ! cin_isatty || ! cout_isatty;
}


wordvec split (const string& line, const string& delimiters) {
   wordvec words;
   size_t end = 0;

   // Loop over the string, splitting out words, and for each word
   // thus found, append it to the output wordvec.
   for (;;) {
      size_t start = line.find_first_not_of (delimiters, end);
      if (start == string::npos) break;
      end = line.find_first_of (delimiters, start);
      words.push_back (line.substr (start, end - start));
   }
   DEBUGF ('u', words);
   return words;
}

//consolidates a wordvec into a single string
/*string wordvecToString(const wordvec& words){
   string out;
   for(unsigned i = 0; i < words.size(); ++i){
      out << words[i];
   }
   return out;
}*/

ostream& complain() {
   exit_status::set (EXIT_FAILURE);
   cerr << execname() << ": ";
   return cerr;
}

