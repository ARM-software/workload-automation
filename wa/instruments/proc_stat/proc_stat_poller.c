/*    Copyright 2018 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/

#include <fcntl.h>
#include <stdio.h>
#include <sys/poll.h>
#include <time.h>
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

typedef struct {
    unsigned long long user;
    unsigned long long nice;
    unsigned long long system;
    unsigned long long idle;
    unsigned long long iowait;
    unsigned long long irq;
    unsigned long long softirq;
    unsigned long long steal;
    unsigned long long guest;
    unsigned long long guest_nice;
} cpu_stats_t;

int write_trace_marker(char *marker, int size)
{
    int ret;
    FILE *file;

    file = fopen("/sys/kernel/debug/tracing/trace_marker", "w");
    if (file == NULL) {
        return -errno;
    }

    ret = fwrite(marker, sizeof(char), size, file);

    fclose(file);
    return ret;
}

int count_cpus(FILE *file) {
    char line[256];
    int cpu_count = 0;

    // Reset file position
    fseek(file, 0, SEEK_SET);

    while (fgets(line, sizeof(line), file) != NULL) {
        int cpu_id;
        if (sscanf(line, "cpu%d", &cpu_id) == 1) {
            cpu_count++;
        }
    }

    return cpu_count;
}

int parse_cpu_stats(FILE *file, cpu_stats_t *aggregate, cpu_stats_t *cpu_data, int num_cpus, int include_per_core) {
    char line[256];
    int cpu_count = 0;

    // Reset file position
    fseek(file, 0, SEEK_SET);

    while (fgets(line, sizeof(line), file) != NULL) {
        if (strncmp(line, "cpu", 3) == 0) {
            // Check if it's the aggregate line (just "cpu ")
            if (line[3] == ' ') {
                sscanf(line, "cpu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu",
                       &aggregate->user,
                       &aggregate->nice,
                       &aggregate->system,
                       &aggregate->idle,
                       &aggregate->iowait,
                       &aggregate->irq,
                       &aggregate->softirq,
                       &aggregate->steal,
                       &aggregate->guest,
                       &aggregate->guest_nice);
            } else if (include_per_core) {
                // It's a per-CPU line
                int cpu_id;
                cpu_stats_t *stats = &cpu_data[cpu_count];

                if (sscanf(line, "cpu%d %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu",
                           &cpu_id,
                           &stats->user,
                           &stats->nice,
                           &stats->system,
                           &stats->idle,
                           &stats->iowait,
                           &stats->irq,
                           &stats->softirq,
                           &stats->steal,
                           &stats->guest,
                           &stats->guest_nice) == 11) {
                    cpu_count++;
                    if (cpu_count >= num_cpus) {
                        break;
                    }
                }
            }
        }
    }

    return cpu_count;
}

void format_iso8601_timestamp(char *buffer, size_t buffer_size, struct timespec *ts) {
    time_t seconds = ts->tv_sec;
    long nanoseconds = ts->tv_nsec;
    struct tm *tm_info;
    char datetime_part[32];
    char tz_offset[8];

    // Convert to local time
    tm_info = localtime(&seconds);

    // Format the date and time part with microseconds
    strftime(datetime_part, sizeof(datetime_part), "%Y-%m-%dT%H:%M:%S", tm_info);

    // Calculate timezone offset
    long timezone_offset = tm_info->tm_gmtoff;
    int hours = timezone_offset / 3600;
    int minutes = abs(timezone_offset % 3600) / 60;

    // Format timezone offset
    snprintf(tz_offset, sizeof(tz_offset), "%+03d:%02d", hours, minutes);

    // Combine into final format with microseconds
    snprintf(buffer, buffer_size, "%s.%06ld%s", datetime_part, nanoseconds / 1000, tz_offset);
}

int main(int argc, char ** argv) {
    extern char *optarg;
    extern int optind;
    int c = 0;
    int show_help = 0;
    useconds_t interval = 1000000;
    struct timespec current_time;
    char timestamp[64];
    int should_write_marker = 0;
    int include_per_core = 0;  // Default to NOT including per-core stats
    int ret;
    int first_reading = 1;

    static char usage[] = "usage: %s [-h] [-m] [-c] [-t INTERVAL]\n"
                          "polls /proc/stat every INTERVAL microseconds and outputs\n"
                          "aggregate CPU statistics in CSV format\n"
                          "\n"
                          "    -h     Display this message\n"
                          "    -m     Insert a marker into ftrace at the time of the first\n"
                          "           sample. This marker may be used to align the timestamps\n"
                          "           produced by the poller with those of ftrace events.\n"
                          "    -c     Enable per-core statistics (in addition to aggregate)\n"
                          "    -t     The polling sample interval in microseconds\n"
                          "           Defaults to 1000000 (1 second)\n";

    // Handling command line arguments
    while ((c = getopt(argc, argv, "hmct:")) != -1)
    {
        switch(c) {
            case 'h':
            case '?':
            default:
                show_help = 1;
                break;
            case 'm':
                should_write_marker = 1;
                break;
            case 'c':
                include_per_core = 1;
                break;
            case 't':
                interval = (useconds_t)atoi(optarg);
                break;
        }
    }

    if (show_help) {
        fprintf(stderr, usage, argv[0]);
        exit(1);
    }

    // Open /proc/stat
    FILE *stat_file = fopen("/proc/stat", "r");
    if (stat_file == NULL) {
        fprintf(stderr, "ERROR: Could not open /proc/stat: %s\n", strerror(errno));
        exit(2);
    }

    // Count CPUs dynamically
    int num_cpus = 0;
    cpu_stats_t *cpu_data = NULL;

    if (include_per_core) {
        num_cpus = count_cpus(stat_file);
        if (num_cpus == 0) {
            fprintf(stderr, "ERROR: No CPU information found in /proc/stat\n");
            fclose(stat_file);
            exit(3);
        }

        fprintf(stderr, "Detected %d CPU cores\n", num_cpus);

        // Dynamically allocate CPU data structures
        cpu_data = calloc(num_cpus, sizeof(cpu_stats_t));
        if (cpu_data == NULL) {
            fprintf(stderr, "ERROR: Failed to allocate memory for %d CPUs\n", num_cpus);
            fclose(stat_file);
            exit(4);
        }
    }

    // Allocate aggregate CPU data
    cpu_stats_t aggregate_stats;
    memset(&aggregate_stats, 0, sizeof(cpu_stats_t));

    // Print headers - aggregate first, then per-CPU if enabled
    printf("timestamp,user,nice,system,idle,"
           "iowait,irq,softirq,steal,guest,guest_nice");

    if (include_per_core) {
        for (int i = 0; i < num_cpus; i++) {
            printf(",cpu%d_user,cpu%d_nice,cpu%d_system,cpu%d_idle,"
                   "cpu%d_iowait,cpu%d_irq,cpu%d_softirq,cpu%d_steal,"
                   "cpu%d_guest,cpu%d_guest_nice",
                   i, i, i, i, i, i, i, i, i, i);
        }
    }
    printf("\n");

    // Setup SIGTERM handler
    struct sigaction action;
    memset(&action, 0, sizeof(struct sigaction));
    action.sa_handler = term;
    sigaction(SIGTERM, &action, NULL);

    // Poll CPU stats
    while (!done) {
        // Get high-resolution timestamp
        clock_gettime(CLOCK_REALTIME, &current_time);

        if (should_write_marker && first_reading) {
            ret = write_trace_marker("CPU_POLLER_START", 16);
            if (ret < 0) {
                fprintf(stderr, "ERROR writing trace marker: %s\n", strerror(-ret));
            }
        }

        // Format timestamp
        format_iso8601_timestamp(timestamp, sizeof(timestamp), &current_time);

        // Read current CPU stats
        parse_cpu_stats(stat_file, &aggregate_stats, cpu_data, num_cpus, include_per_core);

        printf("%s", timestamp);

        // Print aggregate CPU stats
        printf(",%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu",
               aggregate_stats.user,
               aggregate_stats.nice,
               aggregate_stats.system,
               aggregate_stats.idle,
               aggregate_stats.iowait,
               aggregate_stats.irq,
               aggregate_stats.softirq,
               aggregate_stats.steal,
               aggregate_stats.guest,
               aggregate_stats.guest_nice);

        // Print per-CPU stats if enabled
        if (include_per_core) {
            for (int i = 0; i < num_cpus; i++) {
                printf(",%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu",
                       cpu_data[i].user,
                       cpu_data[i].nice,
                       cpu_data[i].system,
                       cpu_data[i].idle,
                       cpu_data[i].iowait,
                       cpu_data[i].irq,
                       cpu_data[i].softirq,
                       cpu_data[i].steal,
                       cpu_data[i].guest,
                       cpu_data[i].guest_nice);
            }
        }
        printf("\n");
        fflush(stdout);

        first_reading = 0;
        usleep(interval);
    }

    // Clean up
    if (cpu_data != NULL) {
        free(cpu_data);
    }
    fclose(stat_file);
    exit(0);
}
