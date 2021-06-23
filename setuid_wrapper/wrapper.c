#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>


void usage() {
    printf("Wrong arguments! No usage, self-explanatory code :)\n");
}


/* Bad and insecure code! Use at your own risk! I'm not responsible for any damages or loss  */
int main(int argc, char ** const argv) {
    char cmd[2048] = {0};

    if (argc < 3 || argc > 4) {
        usage();
        return -1;
    }

    if (strcmp(argv[1], "mount") == 0) {
        strcpy(cmd, "mount ");
        strcat(cmd, argv[2]);
        strcat(cmd, " ");
        strcat(cmd, argv[3]);
    }

    if (strcmp(argv[1], "umount") == 0) {
        strcpy(cmd, "umount ");
        strcat(cmd, argv[2]);
    }

    if (strcmp(argv[1], "chmod") == 0) {
        strcpy(cmd, "chmod -R 777 ");
        strcat(cmd, argv[2]);
    }

    if (strlen(cmd) < 1) {
        usage();
        return -1;
    }

    if (setuid(0) == 0) {
        printf("$ %s\n", cmd);
        return system(cmd);
    } else {
        perror("You must run it as root");
    }

    return 0;
}

