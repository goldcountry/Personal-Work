#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <errno.h>

extern char **get_line(void);

int main(int argc, char *argv[]) {
  int i;
  char **args; 

  while(1) {
    args = get_line();
    if(!args) break;
    for(i = 0; args[i] != NULL; i++) {
      printf("Argument %d: %s\n", i, args[i]);
    }
  }
  return 0;
}