#include <fcntl.h>
#include <stdio.h>
#include <sys/poll.h>
#include <sys/time.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>

volatile sig_atomic_t done = 0;
void term(int signum)
{
    done = 1;
}

int main(int argc, char ** argv) {
    
    extern char *optarg;
    extern int optind;
    int c = 0;
    int show_help = 0;
    useconds_t interval = 1000000;
    char buf[1024];
    memset(buf, 0, sizeof(buf));
    struct timeval current_time;
    double time_float;
    int files_to_poll[argc-optind];
    char *labels;
    int labelCount = 0;
    static char usage[] = "usage: %s [-h] [-t INTERVAL] FILE [FILE ...]\n"
                          "polls FILE(s) every INTERVAL microseconds and outputs\n"
                          "the results in CSV format including a timestamp to STDOUT\n"
                          "\n"
                          "    -h     Display this message\n"
                          "    -t     The polling sample interval in microseconds\n"
                          "           Defaults to 1000000 (1 second)\n"
                          "    -l     Comma separated list of labels to use in the CSV\n"
                          "           output. This should match the number of files\n";
    
    
    //Handling command line arguments
    while ((c = getopt(argc, argv, "ht:l:")) != -1)
    {
        switch(c) {
            case 'h':
            case '?':
            default:
                show_help = 1;
                break;
            case 't':
                interval = (useconds_t)atoi(optarg);
                break;
            case 'l':
                labels = optarg;
                labelCount = 1;
                int i;
                for (i=0; labels[i]; i++)
                    labelCount += (labels[i] == ',');
        }
    }

    if (show_help) {
        fprintf(stderr, usage, argv[0]);
        exit(1);
    }

    if (optind >= argc) {
        fprintf(stderr, "%s: missiing file path(s)\n", argv[0]);
        fprintf(stderr, usage, argv[0]);
        exit(1);
    } 

    if (labelCount && labelCount != argc-optind)
    {
        fprintf(stderr, "%s: %d labels specified but %d files specified\n", argv[0],
                                                                            labelCount,
                                                                            argc-optind);
        fprintf(stderr, usage, argv[0]);
        exit(1);
    }
      
    //Print headers and open files to poll  
    printf("time");
    if(labelCount)
    {
        printf(",%s", labels);
    }
    int i;
    for (i = 0; i < (argc - optind); i++)
    {
        files_to_poll[i] = open(argv[optind + i], O_RDONLY);
        if(!labelCount) {
            printf(",%s", argv[optind + i]);
        }
    }
    printf("\n");    

    //Setup SIGTERM handler
    struct sigaction action;
    memset(&action, 0, sizeof(struct sigaction));
    action.sa_handler = term;
    sigaction(SIGTERM, &action, NULL);

    //Poll files 
    while (!done) {
        gettimeofday(&current_time, NULL); 
        time_float = (double)current_time.tv_sec;
        time_float += ((double)current_time.tv_usec)/1000/1000;
        printf("%f", time_float);
        for (i = 0; i < (argc - optind); i++) {
            read(files_to_poll[i], buf, 1024);
            lseek(files_to_poll[i], 0, SEEK_SET);

            //Removes trailing "\n"
            int new_line = strlen(buf) -1;
            if (buf[new_line] == '\n')
                buf[new_line] = '\0';

            printf(",%s", buf);
        }
        printf("\n");
        usleep(interval);
    }
    
    //Close files
    for (i = 0; i < (argc - optind); i++)
    {
        files_to_poll[i] = open(argv[optind + i], O_RDONLY);
    }
    exit(0);
}
