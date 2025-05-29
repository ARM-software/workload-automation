/*    Copyright 2025 ARM Limited
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

typedef struct
{
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

typedef struct
{
    cpu_stats_t current;
    cpu_stats_t previous;
} cpu_data_t;

int write_trace_marker(char *marker, int size)
{
    int ret;
    FILE *file;

    file = fopen("/sys/kernel/debug/tracing/trace_marker", "w");
    if (file == NULL)
    {
        return -errno;
    }

    ret = fwrite(marker, sizeof(char), size, file);

    fclose(file);
    return ret;
}

unsigned long long get_total_time(cpu_stats_t *stats)
{
    return stats->user + stats->nice + stats->system + stats->idle +
           stats->iowait + stats->irq + stats->softirq + stats->steal +
           stats->guest + stats->guest_nice;
}

unsigned long long get_idle_time(cpu_stats_t *stats)
{
    return stats->idle + stats->iowait;
}

double calculate_cpu_load(cpu_stats_t *current, cpu_stats_t *previous)
{
    unsigned long long total_current = get_total_time(current);
    unsigned long long total_previous = get_total_time(previous);
    unsigned long long idle_current = get_idle_time(current);
    unsigned long long idle_previous = get_idle_time(previous);

    unsigned long long total_diff = total_current - total_previous;
    unsigned long long idle_diff = idle_current - idle_previous;

    if (total_diff == 0)
    {
        return 0.0;
    }

    return 100.0 * (1.0 - ((double)idle_diff / (double)total_diff));
}

int count_cpus(FILE *file)
{
    char line[256];
    int cpu_count = 0;

    while (fgets(line, sizeof(line), file) != NULL)
    {
        int cpu_id;
        if (sscanf(line, "cpu%d", &cpu_id) == 1)
        {
            cpu_count++;
        }
    }

    return cpu_count;
}

int parse_cpu_stats(FILE *file, cpu_data_t *cpu_data, int num_cpus)
{
    char line[256];
    int cpu_count = 0;

    // Reset file position
    fseek(file, 0, SEEK_SET);

    while (fgets(line, sizeof(line), file) != NULL && cpu_count < num_cpus)
    {
        int cpu_id;
        cpu_stats_t *stats = &cpu_data[cpu_count].current;

        // Try to parse the full CPU line with all stats
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
                   &stats->guest_nice) == 11)
        {
            cpu_count++;
        }
    }

    return cpu_count;
}

int main(int argc, char **argv)
{
    extern char *optarg;
    extern int optind;
    int c = 0;
    int show_help = 0;
    useconds_t interval = 1000000;
    struct timespec current_time;
    double time_float;
    int should_write_marker = 0;
    int ret;
    int first_reading = 1;

    static char usage[] = "usage: %s [-h] [-m] [-t INTERVAL]\n"
                          "polls /proc/stat every INTERVAL microseconds and outputs\n"
                          "per-core CPU load in CSV format including a timestamp to STDOUT\n"
                          "\n"
                          "    -h     Display this message\n"
                          "    -m     Insert a marker into ftrace at the time of the first\n"
                          "           sample. This marker may be used to align the timestamps\n"
                          "           produced by the poller with those of ftrace events.\n"
                          "    -t     The polling sample interval in microseconds\n"
                          "           Defaults to 1000000 (1 second)\n";

    // Handling command line arguments
    while ((c = getopt(argc, argv, "hmt:")) != -1)
    {
        switch (c)
        {
        case 'h':
        case '?':
        default:
            show_help = 1;
            break;
        case 'm':
            should_write_marker = 1;
            break;
        case 't':
            interval = (useconds_t)atoi(optarg);
            break;
        }
    }

    if (show_help)
    {
        fprintf(stderr, usage, argv[0]);
        exit(1);
    }

    // Open /proc/stat
    FILE *stat_file = fopen("/proc/stat", "r");
    if (stat_file == NULL)
    {
        fprintf(stderr, "ERROR: Could not open /proc/stat: %s\n", strerror(errno));
        exit(2);
    }

    // Count CPUs dynamically
    int num_cpus = count_cpus(stat_file);
    if (num_cpus == 0)
    {
        fprintf(stderr, "ERROR: No CPU information found in /proc/stat\n");
        fclose(stat_file);
        exit(3);
    }

    fprintf(stderr, "Detected %d CPU cores\n", num_cpus);

    // Dynamically allocate CPU data structures
    cpu_data_t *cpu_data = calloc(num_cpus, sizeof(cpu_data_t));
    if (cpu_data == NULL)
    {
        fprintf(stderr, "ERROR: Failed to allocate memory for %d CPUs\n", num_cpus);
        fclose(stat_file);
        exit(4);
    }

    // Get initial CPU stats and print headers
    parse_cpu_stats(stat_file, cpu_data, num_cpus);
    printf("time");
    for (int i = 0; i < num_cpus; i++)
    {
        printf(",cpu%d_load", i);
    }
    printf("\n");

    // Copy current to previous for first reading
    for (int i = 0; i < num_cpus; i++)
    {
        cpu_data[i].previous = cpu_data[i].current;
    }

    // Setup SIGTERM handler
    struct sigaction action;
    memset(&action, 0, sizeof(struct sigaction));
    action.sa_handler = term;
    sigaction(SIGTERM, &action, NULL);

    // Poll CPU stats
    while (!done)
    {
        clock_gettime(CLOCK_BOOTTIME, &current_time);

        if (should_write_marker && first_reading)
        {
            ret = write_trace_marker("CPU_POLLER_START", 16);
            if (ret < 0)
            {
                fprintf(stderr, "ERROR writing trace marker: %s\n", strerror(-ret));
            }
        }

        // Read current CPU stats
        parse_cpu_stats(stat_file, cpu_data, num_cpus);

        time_float = (double)current_time.tv_sec;
        time_float += ((double)current_time.tv_nsec) / 1000000000.0;
        printf("%f", time_float);

        // Calculate and print CPU load for each core
        for (int i = 0; i < num_cpus; i++)
        {
            double load = 0.0;
            if (!first_reading)
            {
                load = calculate_cpu_load(&cpu_data[i].current, &cpu_data[i].previous);
            }
            printf(",%.2f", load);

            // Update previous stats
            cpu_data[i].previous = cpu_data[i].current;
        }
        printf("\n");
        fflush(stdout);

        first_reading = 0;
        usleep(interval);
    }

    // Clean up
    free(cpu_data);
    fclose(stat_file);
    exit(0);
}
