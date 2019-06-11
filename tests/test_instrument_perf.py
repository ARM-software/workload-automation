#    copyright 2019 Arm limited
#
# licensed under the apache license, version 2.0 (the "license");
# you may not use this file except in compliance with the license.
# you may obtain a copy of the license at
#
#     http://www.apache.org/licenses/license-2.
#
# unless required by applicable law or agreed to in writing, software
# distributed under the license is distributed on an "as is" basis,
# without warranties or conditions of any kind, either express or implied.
# see the license for the specific language governing permissions and
# limitations under the license.

import unittest

from wa.instruments.perf import PerfInstrument

STAT_PAIRS = {

    '-a -e r1,r2,r3,r4,r5,r6,r7,r8': [
(
# Pixel 2 - OS 4.4.88-ga1592dc22912
# perf version 3.9.rc8.ge9aa1d6
"""
 Performance counter stats for 'sleep 1000':

              1139 migrations                                                   [100.00%]
              6141 cs
          14648295 r1                                                           [74.87%]
           2966422 r2                                                           [74.96%]
          11872707 r3                                                           [74.94%]
        8184054637 r4                                                           [75.11%]
           2409014 r5                                                           [75.30%]
          86957873 r6                                                           [75.27%]
          34552449 r7                                                           [75.14%]
       15730113018 r8                                                           [74.88%]

       1.681693229 seconds time elapsed
""",
[
    {
	"name": "default0_migrations",
	"value": 1139,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs",
	"value": 6141,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "cs"
	}
    },
    {
	"name": "default0_r1",
	"value": 14648295,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r1",
	    "enabled": 74.87
	}
    },
    {
	"name": "default0_r2",
	"value": 2966422,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r2",
	    "enabled": 74.96
	}
    },
    {
	"name": "default0_r3",
	"value": 11872707,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r3",
	    "enabled": 74.94
	}
    },
    {
	"name": "default0_r4",
	"value": 8184054637,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r4",
	    "enabled": 75.11
	}
    },
    {
	"name": "default0_r5",
	"value": 2409014,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r5",
	    "enabled": 75.3
	}
    },
    {
	"name": "default0_r6",
	"value": 86957873,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r6",
	    "enabled": 75.27
	}
    },
    {
	"name": "default0_r7",
	"value": 34552449,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r7",
	    "enabled": 75.14
	}
    },
    {
	"name": "default0_r8",
	"value": 15730113018,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 1.681693229,
	    "duration_units": "seconds",
	    "name": "r8",
	    "enabled": 74.88
	}
    }
],
),
],

    '-a -A': [
(
# Pixel 2 - OS 4.4.88-ga1592dc22912
# perf version 3.9.rc8.ge9aa1d6
"""
 Performance counter stats for 'sleep 1000':

 CPU0                   201 migrations                                                    (100.00%)
 CPU1                   217 migrations                                                    (100.00%)
 CPU2                   241 migrations                                                    (100.00%)
 CPU3                   216 migrations                                                    (100.00%)
 CPU4                    79 migrations                                                    (100.00%)
 CPU5                    40 migrations                                                    (100.00%)
 CPU6                    55 migrations                                                    (100.00%)
 CPU7                    70 migrations                                                    (100.00%)
 CPU0                  2285 cs
 CPU1                  1454 cs
 CPU2                  2704 cs
 CPU3                  2085 cs
 CPU4                  1790 cs
 CPU5                  1240 cs
 CPU6                   636 cs
 CPU7                  1557 cs

        2.494999050 seconds time elapsed
""",
[
    {
	"name": "default0_migrations_T0",
	"value": 201,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 0,
	    "hw_thread_count": 1,
	    "cpu": 0,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T1",
	"value": 217,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 1,
	    "hw_thread_count": 1,
	    "cpu": 1,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T2",
	"value": 241,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 2,
	    "hw_thread_count": 1,
	    "cpu": 2,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T3",
	"value": 216,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 3,
	    "hw_thread_count": 1,
	    "cpu": 3,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T4",
	"value": 79,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 4,
	    "hw_thread_count": 1,
	    "cpu": 4,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T5",
	"value": 40,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 5,
	    "hw_thread_count": 1,
	    "cpu": 5,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T6",
	"value": 55,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 6,
	    "hw_thread_count": 1,
	    "cpu": 6,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_migrations_T7",
	"value": 70,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "hw_thread": 7,
	    "hw_thread_count": 1,
	    "cpu": 7,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs_T0",
	"value": 2285,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 0,
	    "hw_thread_count": 1,
	    "cpu": 0
	}
    },
    {
	"name": "default0_cs_T1",
	"value": 1454,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 1,
	    "hw_thread_count": 1,
	    "cpu": 1
	}
    },
    {
	"name": "default0_cs_T2",
	"value": 2704,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 2,
	    "hw_thread_count": 1,
	    "cpu": 2
	}
    },
    {
	"name": "default0_cs_T3",
	"value": 2085,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 3,
	    "hw_thread_count": 1,
	    "cpu": 3
	}
    },
    {
	"name": "default0_cs_T4",
	"value": 1790,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 4,
	    "hw_thread_count": 1,
	    "cpu": 4
	}
    },
    {
	"name": "default0_cs_T5",
	"value": 1240,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 5,
	    "hw_thread_count": 1,
	    "cpu": 5
	}
    },
    {
	"name": "default0_cs_T6",
	"value": 636,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 6,
	    "hw_thread_count": 1,
	    "cpu": 6
	}
    },
    {
	"name": "default0_cs_T7",
	"value": 1557,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.49499905,
	    "duration_units": "seconds",
	    "name": "cs",
	    "hw_thread": 7,
	    "hw_thread_count": 1,
	    "cpu": 7
	}
    }
],
),
],

    '-a -A --per-socket': [
(
# Pixel 2 - OS 4.4.88-ga1592dc22912
# perf version 3.9.rc8.ge9aa1d6
"""
 Performance counter stats for 'sleep 1000':

S0        4                697 migrations                                                    (100.00%)
S0        4               7801 cs
S1        4                203 migrations                                                    (100.00%)
S1        4               4408 cs

       2.262571267 seconds time elapsed
""",
[
    {
	"name": "default0_migrations_S0",
	"value": 697,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.262571267,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs_S0",
	"value": 7801,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.262571267,
	    "duration_units": "seconds",
	    "name": "cs",
	    "cluster": 0,
	    "hw_thread_count": 4
	}
    },
    {
	"name": "default0_migrations_S1",
	"value": 203,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.262571267,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs_S1",
	"value": 4408,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.262571267,
	    "duration_units": "seconds",
	    "name": "cs",
	    "cluster": 1,
	    "hw_thread_count": 4
	}
    }
],
),
],
    "-a -A -e r1,r2,r3,r4,r5,r6,r7,r8 --per-socket": [
(
# Pixel 2 - OS 4.4.88-ga1592dc22912
# perf version 3.9.rc8.ge9aa1d6
"""
 Performance counter stats for 'sleep 1000':

S0        4                725 migrations                                                    (100.00%)
S0        4               7202 cs
S0        4            9439048 r1                                                            (37.55%)
S0        4             179650 r2                                                            (37.54%)
S0        4            3856583 r3                                                            (37.56%)
S0        4           71399486 r4                                                            (37.49%)
S0        4             251669 r5                                                            (37.48%)
S0        4           39189196 r6                                                            (37.46%)
S0        4           19239860 r7                                                            (37.47%)
S0        4          288165417 r8                                                            (37.47%)
S1        4                222 migrations                                                    (100.00%)
S1        4               5225 cs
S1        4            8222810 r1                                                            (37.55%)
S1        4            2852407 r2                                                            (37.55%)
S1        4            5519117 r3                                                            (37.55%)
S1        4         7193421718 r4                                                            (37.49%)
S1        4            3236589 r5                                                            (37.47%)
S1        4                  0 r6                                                            (37.47%)
S1        4                  0 r7                                                            (37.47%)
S1        4        13821910139 r8                                                            (37.47%)

       2.256465902 seconds time elapsed
""",
[
    {
	"name": "default0_migrations_S0",
	"value": 725,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs_S0",
	"value": 7202,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "cs",
	    "cluster": 0,
	    "hw_thread_count": 4
	}
    },
    {
	"name": "default0_r1_S0",
	"value": 9439048,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r1",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.55
	}
    },
    {
	"name": "default0_r2_S0",
	"value": 179650,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r2",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.54
	}
    },
    {
	"name": "default0_r3_S0",
	"value": 3856583,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r3",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.56
	}
    },
    {
	"name": "default0_r4_S0",
	"value": 71399486,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r4",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.49
	}
    },
    {
	"name": "default0_r5_S0",
	"value": 251669,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r5",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.48
	}
    },
    {
	"name": "default0_r6_S0",
	"value": 39189196,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r6",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.46
	}
    },
    {
	"name": "default0_r7_S0",
	"value": 19239860,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r7",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    },
    {
	"name": "default0_r8_S0",
	"value": 288165417,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r8",
	    "cluster": 0,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    },
    {
	"name": "default0_migrations_S1",
	"value": 222,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "migrations",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 100.0
	}
    },
    {
	"name": "default0_cs_S1",
	"value": 5225,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "cs",
	    "cluster": 1,
	    "hw_thread_count": 4
	}
    },
    {
	"name": "default0_r1_S1",
	"value": 8222810,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r1",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.55
	}
    },
    {
	"name": "default0_r2_S1",
	"value": 2852407,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r2",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.55
	}
    },
    {
	"name": "default0_r3_S1",
	"value": 5519117,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r3",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.55
	}
    },
    {
	"name": "default0_r4_S1",
	"value": 7193421718,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r4",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.49
	}
    },
    {
	"name": "default0_r5_S1",
	"value": 3236589,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r5",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    },
    {
	"name": "default0_r6_S1",
	"value": 0,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r6",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    },
    {
	"name": "default0_r7_S1",
	"value": 0,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r7",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    },
    {
	"name": "default0_r8_S1",
	"value": 13821910139,
	"units": None,
	"classifiers": {
	    "label": "default0",
	    "target": "'sleep 1000'",
	    "duration": 2.256465902,
	    "duration_units": "seconds",
	    "name": "r8",
	    "cluster": 1,
	    "hw_thread_count": 4,
	    "enabled": 37.47
	}
    }
],
),
],

    '-a -A --per-core': [
(
# Ubuntu 18.04.2 LTS - OS 4.15.0-50-generic
# perf version 4.15.18
"""
 Performance counter stats for 'system wide':

S0-C0           2        2003.008100      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C0           2                 38      context-switches          #    0.019 K/sec
S0-C0           2                  3      cpu-migrations            #    0.001 K/sec
S0-C0           2                 73      page-faults               #    0.036 K/sec
S0-C0           2         15,750,905      cycles                    #    0.008 GHz
S0-C0           2          4,042,693      instructions              #    0.26  insn per cycle
S0-C0           2            860,481      branches                  #    0.430 M/sec
S0-C0           2            166,940      branch-misses             #   19.40% of all branches
S0-C1           2        2003.042586      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C1           2                155      context-switches          #    0.077 K/sec
S0-C1           2                  1      cpu-migrations            #    0.000 K/sec
S0-C1           2                386      page-faults               #    0.193 K/sec
S0-C1           2        407,532,423      cycles                    #    0.203 GHz
S0-C1           2         73,526,057      instructions              #    0.18  insn per cycle
S0-C1           2         22,478,777      branches                  #   11.222 M/sec
S0-C1           2            293,815      branch-misses             #    1.31% of all branches
S0-C2           2        2003.076028      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C2           2                213      context-switches          #    0.106 K/sec
S0-C2           2                  2      cpu-migrations            #    0.001 K/sec
S0-C2           2                  1      page-faults               #    0.000 K/sec
S0-C2           2         18,605,672      cycles                    #    0.009 GHz
S0-C2           2          4,406,356      instructions              #    0.24  insn per cycle
S0-C2           2          1,088,504      branches                  #    0.543 M/sec
S0-C2           2            142,203      branch-misses             #   13.06% of all branches
S0-C3           2        2003.109192      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C3           2                245      context-switches          #    0.122 K/sec
S0-C3           2                  6      cpu-migrations            #    0.003 K/sec
S0-C3           2                  0      page-faults               #    0.000 K/sec
S0-C3           2         23,626,131      cycles                    #    0.012 GHz
S0-C3           2          7,714,748      instructions              #    0.33  insn per cycle
S0-C3           2          1,805,933      branches                  #    0.902 M/sec
S0-C3           2            193,243      branch-misses             #   10.70% of all branches
S0-C4           2        2003.143584      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C4           2                596      context-switches          #    0.298 K/sec
S0-C4           2                  6      cpu-migrations            #    0.003 K/sec
S0-C4           2                113      page-faults               #    0.056 K/sec
S0-C4           2         53,837,367      cycles                    #    0.027 GHz
S0-C4           2         23,264,962      instructions              #    0.43  insn per cycle
S0-C4           2          4,975,165      branches                  #    2.484 M/sec
S0-C4           2            301,069      branch-misses             #    6.05% of all branches
S0-C5           2        2003.151837      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C5           2                172      context-switches          #    0.086 K/sec
S0-C5           2                  4      cpu-migrations            #    0.002 K/sec
S0-C5           2                 37      page-faults               #    0.018 K/sec
S0-C5           2         24,086,889      cycles                    #    0.012 GHz
S0-C5           2          7,219,194      instructions              #    0.30  insn per cycle
S0-C5           2          1,537,648      branches                  #    0.768 M/sec
S0-C5           2            177,565      branch-misses             #   11.55% of all branches
S0-C6           2        2003.160900      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C6           2                146      context-switches          #    0.073 K/sec
S0-C6           2                  3      cpu-migrations            #    0.001 K/sec
S0-C6           2                 69      page-faults               #    0.034 K/sec
S0-C6           2         27,327,018      cycles                    #    0.014 GHz
S0-C6           2          7,956,363      instructions              #    0.29  insn per cycle
S0-C6           2          1,834,119      branches                  #    0.916 M/sec
S0-C6           2            210,607      branch-misses             #   11.48% of all branches
S0-C7           2        2003.187967      cpu-clock (msec)          #    1.998 CPUs utilized
S0-C7           2                 91      context-switches          #    0.045 K/sec
S0-C7           2                  1      cpu-migrations            #    0.000 K/sec
S0-C7           2                 32      page-faults               #    0.016 K/sec
S0-C7           2         26,120,485      cycles                    #    0.013 GHz
S0-C7           2         10,457,563      instructions              #    0.40  insn per cycle
S0-C7           2          2,337,445      branches                  #    1.167 M/sec
S0-C7           2            238,864      branch-misses             #   10.22% of all branches

       1.002350964 seconds time elapsed
""",
[
    {
        "name": "default0_cpu-clock_(msec)_S0_C0",
        "units": None,
        "value": 2003.0081,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C0",
        "units": None,
        "value": 38,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.019,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C0",
        "units": None,
        "value": 3,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.001,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C0",
        "units": None,
        "value": 73,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.036,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C0",
        "units": None,
        "value": 15750905,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.008,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C0",
        "units": None,
        "value": 4042693,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.26,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C0",
        "units": None,
        "value": 860481,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 0.43,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C0",
        "units": None,
        "value": 166940,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 0,
            "comment_value": 19.4,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C1",
        "units": None,
        "value": 2003.042586,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C1",
        "units": None,
        "value": 155,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 0.077,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C1",
        "units": None,
        "value": 1,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 0.0,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C1",
        "units": None,
        "value": 386,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 0.193,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C1",
        "units": None,
        "value": 407532423,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 0.203,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C1",
        "units": None,
        "value": 73526057,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 0.18,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C1",
        "units": None,
        "value": 22478777,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 11.222,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C1",
        "units": None,
        "value": 293815,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 1,
            "comment_value": 1.31,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C2",
        "units": None,
        "value": 2003.076028,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C2",
        "units": None,
        "value": 213,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.106,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C2",
        "units": None,
        "value": 2,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.001,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C2",
        "units": None,
        "value": 1,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.0,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C2",
        "units": None,
        "value": 18605672,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.009,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C2",
        "units": None,
        "value": 4406356,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.24,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C2",
        "units": None,
        "value": 1088504,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 0.543,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C2",
        "units": None,
        "value": 142203,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 2,
            "comment_value": 13.06,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C3",
        "units": None,
        "value": 2003.109192,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C3",
        "units": None,
        "value": 245,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.122,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C3",
        "units": None,
        "value": 6,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.003,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C3",
        "units": None,
        "value": 0,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.0,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C3",
        "units": None,
        "value": 23626131,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.012,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C3",
        "units": None,
        "value": 7714748,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.33,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C3",
        "units": None,
        "value": 1805933,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 0.902,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C3",
        "units": None,
        "value": 193243,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 3,
            "comment_value": 10.7,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C4",
        "units": None,
        "value": 2003.143584,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C4",
        "units": None,
        "value": 596,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 0.298,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C4",
        "units": None,
        "value": 6,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 0.003,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C4",
        "units": None,
        "value": 113,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 0.056,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C4",
        "units": None,
        "value": 53837367,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 0.027,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C4",
        "units": None,
        "value": 23264962,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 0.43,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C4",
        "units": None,
        "value": 4975165,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 2.484,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C4",
        "units": None,
        "value": 301069,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 4,
            "comment_value": 6.05,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C5",
        "units": None,
        "value": 2003.151837,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C5",
        "units": None,
        "value": 172,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.086,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C5",
        "units": None,
        "value": 4,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.002,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C5",
        "units": None,
        "value": 37,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.018,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C5",
        "units": None,
        "value": 24086889,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.012,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C5",
        "units": None,
        "value": 7219194,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.3,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C5",
        "units": None,
        "value": 1537648,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 0.768,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C5",
        "units": None,
        "value": 177565,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 5,
            "comment_value": 11.55,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C6",
        "units": None,
        "value": 2003.1609,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C6",
        "units": None,
        "value": 146,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.073,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C6",
        "units": None,
        "value": 3,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.001,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C6",
        "units": None,
        "value": 69,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.034,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C6",
        "units": None,
        "value": 27327018,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.014,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C6",
        "units": None,
        "value": 7956363,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.29,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C6",
        "units": None,
        "value": 1834119,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 0.916,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C6",
        "units": None,
        "value": 210607,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 6,
            "comment_value": 11.48,
            "comment_units": "% of all branches"
        }
    },
    {
        "name": "default0_cpu-clock_(msec)_S0_C7",
        "units": None,
        "value": 2003.187967,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-clock (msec)",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 1.998,
            "comment_units": "CPUs utilized"
        }
    },
    {
        "name": "default0_context-switches_S0_C7",
        "units": None,
        "value": 91,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "context-switches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 0.045,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cpu-migrations_S0_C7",
        "units": None,
        "value": 1,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cpu-migrations",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 0.0,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_page-faults_S0_C7",
        "units": None,
        "value": 32,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "page-faults",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 0.016,
            "comment_units": "K/sec"
        }
    },
    {
        "name": "default0_cycles_S0_C7",
        "units": None,
        "value": 26120485,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "cycles",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 0.013,
            "comment_units": "GHz"
        }
    },
    {
        "name": "default0_instructions_S0_C7",
        "units": None,
        "value": 10457563,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "instructions",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 0.4,
            "comment_units": "insn per cycle"
        }
    },
    {
        "name": "default0_branches_S0_C7",
        "units": None,
        "value": 2337445,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branches",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 1.167,
            "comment_units": "M/sec"
        }
    },
    {
        "name": "default0_branch-misses_S0_C7",
        "units": None,
        "value": 238864,
        "classifiers": {
            "label": "default0",
            "target": "'system wide'",
            "duration": 1.002350964,
            "duration_units": "seconds",
            "name": "branch-misses",
            "cluster": 0,
            "hw_thread_count": 2,
            "core": 7,
            "comment_value": 10.22,
            "comment_units": "% of all branches"
        }
    }
],
),
],

}



class StatParserTest(unittest.TestCase):

    maxDiff = None

    def _test_pair(self, stdout, metrics):
        metrics_dut = PerfInstrument._extract_stat_metrics('default0', stdout)
        count = 0
        for metric_dut in metrics_dut:
            # metric names are guaranteed to be unique by the documentation
            metric = next(m for m in metrics if m['name'] == metric_dut['name'])
            self.assertEqual(metric, metric_dut)
            count += 1
        self.assertEqual(count, len(metrics))

    def _test_key(self, key):
        for stdout, metrics in STAT_PAIRS[key]:
            self._test_pair(stdout, metrics)

    def test_all_cpus_many_events(self):
        self._test_key('-a -e r1,r2,r3,r4,r5,r6,r7,r8')

    def test_all_cpus_no_aggregate_per_core(self):
        self._test_key('-a -A --per-core')

    def test_all_cpus_no_aggregate_per_socket(self):
        self._test_key('-a -A --per-socket')

    def test_all_cpus_no_aggregate_many_events_per_socket(self):
        self._test_key('-a -A -e r1,r2,r3,r4,r5,r6,r7,r8 --per-socket')
