#!/bin/sh
#
# Tool for running a suspend/resume on android
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors:
#    Todd Brandt <todd.e.brandt@linux.intel.com>
#

KVERSION=""
MODES=""
MODE="mem"
RTCPATH=""
TPATH="/sys/kernel/debug/tracing"
EPATH="/sys/kernel/debug/tracing/events/power"
FTRACECHECK="yes"
TRACEEVENTS="yes"
HEADER=""
FTRACE="ftrace.txt"
DMESG="dmesg.txt"
LOGFILE="log.txt"
WAKETIME=""
DISPLAY=""

checkDisplay() {
	SCRSTAT=`dumpsys power 2>&1 | grep mScreenOn`
	if [ -n "$SCRSTAT" ]; then
		for i in $SCRSTAT; do break; done
		if [ $i = "mScreenOn=false" ]; then
			DISPLAY="OFF"
		else
			DISPLAY="ON"
		fi
	fi
}

checkFileRead() {
	if [ ! -e $1 ]; then
		onError "$1 not found"
	fi
	if [ ! -r $1 ]; then
		onError "$1 not readable"
	fi
}

checkFileWrite() {
	if [ ! -e $1 ]; then
		onError "$1 not found"
	fi
	if [ ! -w $1 ]; then
		onError "$1 not writeable"
	fi
}

writeToSysFile() {
	if [ ! -e $1 ]; then
		onError "$1 not found"
	fi
	if [ ! -w $1 ]; then
		onError "$1 not writeable"
	fi
	echo "$2" > "$1"
	logEntry "$1 = \"$2\""
}

checkStatus() {
	CHECK="no"
	for m in $MODES; do
		if [ $m = "$MODE" ]; then
			CHECK="yes"
		fi
	done
	if [ $CHECK != "yes" ]; then
		onError "mode ($MODE) is not supported"
	fi
	if [ $FTRACECHECK != "yes" ]; then
		echo " ERROR: ftrace is unsupported {"
		echo "     Please rebuild the kernel with these config options:"
		echo "         CONFIG_FTRACE=y"
		echo "         CONFIG_FUNCTION_TRACER=y"
		echo "         CONFIG_FUNCTION_GRAPH_TRACER=y"
		echo " }"
		exit
	fi
	if [ $TRACEEVENTS != "yes" ]; then
		echo " ERROR: trace events missing {"
		echo "    Please rebuild the kernel with the proper config patches"
		echo "    https://github.com/01org/pm-graph/tree/master/config"
		echo " }"
		exit
	fi
	if [ -n "$WAKETIME" -a -z "$RTCPATH" ]; then
		onError "rtcwake isn't available"
	fi
	if [ ! -w $PWD ]; then
		onError "read-only permissions for this folder"
	fi
}

printStatus() {
	echo "host    : $HOSTNAME"
	echo "kernel  : $KVERSION"
	echo "modes   : $MODES"
	checkDisplay
	if [ -n "$DISPLAY" ]; then
		echo "display : $DISPLAY"
	fi
	if [ -n "$RTCPATH" ]; then
		echo "rtcwake : SUPPORTED"
	else
		echo "rtcwake : NOT SUPPORTED (no rtc wakealarm found)"
	fi
	if [ $FTRACECHECK != "yes" ]; then
		echo " ftrace: NOT SUPPORTED (this is bad) {"
		echo "     Please rebuild the kernel with these config options:"
		echo "         CONFIG_FTRACE=y"
		echo "         CONFIG_FUNCTION_TRACER=y"
		echo "         CONFIG_FUNCTION_GRAPH_TRACER=y"
		echo " }"
	else
		echo "ftrace  : SUPPORTED"
		echo "trace events {"
		files="suspend_resume device_pm_callback_end device_pm_callback_start"
		for f in $files; do
			if [ -e "$EPATH/$f" ]; then
				echo "    $f: FOUND"
			else
				echo "    $f: MISSING"
			fi
		done
		if [ $TRACEEVENTS != "yes" ]; then
			echo ""
			echo "    one or more trace events missing!"
			echo "    Please rebuild the kernel with the proper config patches"
			echo "    https://github.com/01org/pm-graph/tree/master/config"
		fi
		echo "}"
	fi
	if [ $FTRACECHECK = "yes" -a $TRACEEVENTS = "yes" ]; then
		echo "status  : GOOD (you can test suspend/resume)"
	else
		echo "status  : BAD (system needs to be reconfigured for suspend/resume)"
	fi
}

init() {
	if [ -z "$HOSTNAME" ]; then
		HOSTNAME=`hostname 2>/dev/null`
	fi
	checkFileRead "/proc/version"
	# sometimes awk and sed are missing
	for i in `cat /proc/version`; do
		if [ $i != "Linux" -a $i != "version" ]; then
			KVERSION=$i
			break
		fi
	done
	checkFileRead "/sys/power/state"
	MODES=`cat /sys/power/state`
	RTCPATH="/sys/class/rtc/rtc0"
	if [ -e "$RTCPATH" ]; then
		if [ ! -e "$RTCPATH" -o ! -e "$RTCPATH/since_epoch" -o \
			 ! -e "$RTCPATH/wakealarm" ]; then
			RTCPATH=""
		fi
	fi
	files="buffer_size_kb current_tracer trace trace_clock trace_marker \
			trace_options tracing_on available_filter_functions \
			set_ftrace_filter set_graph_function"
	for f in $files; do
		if [ ! -e "$TPATH/$f" ]; then
			FTRACECHECK="no"
		fi
	done
	files="suspend_resume device_pm_callback_end device_pm_callback_start"
	for f in $files; do
		if [ ! -e "$EPATH/$f" ]; then
			TRACEEVENTS="no"
		fi
	done
	STAMP=`date "+suspend-%m%d%y-%H%M%S"`
	HEADER="# $STAMP $HOSTNAME $MODE $KVERSION"
}

setAlarm() {
	if [ -z "$WAKETIME" ]; then
		return
	fi
	checkFileRead "$RTCPATH/since_epoch"
	writeToSysFile "$RTCPATH/wakealarm" "0"
	NOW=`cat $RTCPATH/since_epoch`
	FUTURE=$(($NOW+$WAKETIME))
	writeToSysFile "$RTCPATH/wakealarm" "$FUTURE"
}

printHeader() {
	echo ""
	echo "------------------------------------"
	echo "     Suspend/Resume timing test     "
	echo "------------------------------------"
	echo "hostname   : $HOSTNAME"
	echo "kernel     : $KVERSION"
	echo "mode       : $MODE"
	echo "ftrace out : $PWD/$FTRACE"
	echo "dmesg out  : $PWD/$DMESG"
	echo "log file   : $PWD/$LOGFILE"
	echo "------------------------------------"
}

printHelp() {
	echo ""
	echo "USAGE: android.sh command <args>"
	echo ""
	echo "COMMANDS:"
	echo ""
	echo "  help"
	echo "    print this help text"
	echo ""
	echo "  status"
	echo "    check that the system is configured properly"
	echo ""
	echo "  capture-start"
	echo "    prepare the system to capture data on the next suspend/resume"
	echo "    the user should then initiate a normal suspend/resume"
	echo ""
	echo "  capture-end"
	echo "    collect the data that's been captured in ftrace"
	echo "    the data can then be processed by analyze_suspend"
	echo ""
	echo "  suspend <mem/freeze/standby/disk> [waketime]"
	echo "    force a suspend/resume and gather ftrace/dmesg data"
	echo "    - mode        : suspend mode (required)"
	echo "    - waketime    : wakeup alarm time in seconds (optional)"
	echo ""
}

onError() {
	echo "ERROR: $1"
	exit
}

logStart() {
	echo "------------------------------------" > $LOGFILE
	echo "hostname   : $HOSTNAME" >> $LOGFILE
	echo "kernel     : $KVERSION" >> $LOGFILE
	echo "mode       : $MODE" >> $LOGFILE
	echo "ftrace out : $PWD/$FTRACE" >> $LOGFILE
	echo "dmesg out  : $PWD/$DMESG" >> $LOGFILE
	echo "log file   : $PWD/$LOGFILE" >> $LOGFILE
	echo "------------------------------------" >> $LOGFILE
	date "+%T: logging started" >> $LOGFILE
}

logEnd() {
	date "+%T: logging finished" >> $LOGFILE
}

logEntry() {
	LINE=`date "+%T: $1"`
	echo "$LINE" >> $LOGFILE
	if [ "$2" = "show" ]; then
		echo "$LINE"
	fi
}

suspendPrepare() {
	printHeader
	checkDisplay
	if [ "$DISPLAY" = "OFF" ]; then
		logEntry "waking up the display" "show"
		input keyevent 26
	fi
	logEntry "ftrace setup start" "show"
	rm -f $DMESG
	rm -f $FTRACE
	echo -n `date "+%T: ftrace is being configured"`
	writeToSysFile "$TPATH/tracing_on" "0"
	echo -n "."
	writeToSysFile "$TPATH/trace_clock" "global"
	echo -n "."
	writeToSysFile "$TPATH/current_tracer" "nop"
	echo -n "."
	writeToSysFile "$TPATH/buffer_size_kb" "1000"
	echo -n "."
	writeToSysFile "$EPATH/suspend_resume/enable" "1"
	echo -n "."
	writeToSysFile "$EPATH/device_pm_callback_end/enable" "1"
	echo -n "."
	writeToSysFile "$EPATH/device_pm_callback_start/enable" "1"
	echo -n "."
	writeToSysFile "$TPATH/trace" ""
	echo -n "."
	dmesg -c > /dev/null
	echo "done"
	logEntry "ftrace setup complete" "show"
	writeToSysFile "$TPATH/tracing_on" "1"
	logEntry "ftrace is ON"
	logEntry "waiting to capture suspend/resume data..." "show"
}

suspendComplete() {
	echo ""
	logEntry "checking for suspend/resume data..." "show"
	logEntry "ftrace is OFF"
	checkFileRead "$TPATH/trace"
	writeToSysFile "$TPATH/tracing_on" "0"
	logEntry "capturing $FTRACE" "show"
	echo $HEADER > $FTRACE
	cat $TPATH/trace >> $FTRACE
	logEntry "flushing the ftrace buffer"
	writeToSysFile "$TPATH/trace" ""
	logEntry "capturing $DMESG" "show"
	echo $HEADER >> $DMESG
	logEntry "flushing the dmesg buffer"
	dmesg -c > $DMESG
	n=0
	while read -r line
	do
		n=$(($n+1))
		if [ $n -gt 12 ]; then break; fi
	done < $FTRACE
	if [ $n -le 12 ]; then
		logEntry "NO FTRACE DATA FOUND" "show"
		echo ""
		echo "There's been no PM activity since capture-start was called"
		echo ""
	else
		logEntry "FTRACE DATA IS AVAILABLE" "show"
		echo ""
		echo "You can retrieve the data with adb"
		echo "adb pull $PWD/$FTRACE"
		echo "adb pull $PWD/$DMESG"
		echo "adb pull $PWD/$LOGFILE"
		echo ""
		echo "Run analyze_suspend on the ftrace data to produce an output.html"
		echo "analyze_suspend.py -ftrace ftrace.txt"
		echo ""
	fi
}

forceSuspend() {
	checkFileWrite "/sys/power/state"
	checkFileWrite "$TPATH/trace_marker"
	suspendPrepare
	NOW=`date "+%T"`
	if [ -z "$WAKETIME" ]; then
		echo "SUSPEND START @ $NOW (press a key to resume)"
	else
		echo "SUSPEND START @ $NOW (rtcwake in $WAKETIME seconds)"
		setAlarm
	fi
	echo "<adb connection will now terminate>"
	writeToSysFile "$TPATH/trace_marker" "SUSPEND START"
	logEntry "suspend start"
	# execution will pause here
	writeToSysFile "/sys/power/state" "$MODE"
	logEntry "resume end"
	writeToSysFile "$TPATH/trace_marker" "RESUME COMPLETE"
	suspendComplete
}

if [ $# -lt 1 ]; then
	printHelp
	exit
fi

COMMAND=$1
shift
case "$COMMAND" in
	help)
		printHelp
	;;
	status)
		init
		printStatus
	;;
	capture-start)
		init
		checkStatus
		logStart
		suspendPrepare
		echo ""
		echo "READY TO GO!"
		echo ""
		echo "1) exit adb shell"
		echo "2) disconnect the usb cable"
		echo "3) allow the device to suspend by timing out"
		echo "4) wake the device back up"
		echo "5) reconnect and run 'sh android.sh capture-end'"
		echo ""
	;;
	capture-end)
		init
		checkStatus
		suspendComplete
		logEnd
	;;
	suspend)
		if [ $# -lt 1 ]; then
			printHelp
			echo ""
			onError "suspend requires a mode (i.e. mem)"
		fi
		MODE=$1
		if [ $# -gt 1 ]; then
			WAKETIME=$2
			CHECK=$((0+$WAKETIME))
			if [ $CHECK -le 0 ]; then
				onError "$WAKETIME is not a valid positive integer"
			fi
		fi
		logStart
		init
		checkStatus
		forceSuspend
		logEnd
	;;
	*)
		printHelp
		echo ""
		onError "Invalid command ($COMMAND)"
	;;
esac
