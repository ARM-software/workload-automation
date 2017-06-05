#!/bin/bash

# CD into build dir if possible - allows building from any directory
script_path='.'
if `readlink -f $0 &>/dev/null`; then
    script_path=`readlink -f $0 2>/dev/null`
fi
script_dir=`dirname $script_path`
cd $script_dir

# Ensure gradelw exists before starting
if [[ ! -f gradlew ]]; then
    echo 'gradlew file not found! Check that you are in the right directory.'
    exit 9
fi

# Copy base class library from wlauto dist
libs_dir=app/libs
base_classes=`python -c "import os, wlauto; print os.path.join(os.path.dirname(wlauto.__file__), 'common', 'android', '*.aar')"`
mkdir -p $libs_dir
cp $base_classes $libs_dir

# Build and return appropriate exit code if failed
# gradle build
./gradlew clean :app:assembleDebug
exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    echo "ERROR: 'gradle build' exited with code $exit_code"
    exit $exit_code
fi

# If successful move APK file to workload folder (overwrite previous)
package=com.arm.wlauto.uiauto.gmail
rm -f ../$package
if [[ -f app/build/apk/$package.apk ]]; then
    cp app/build/apk/$package.apk ../$package.apk
else
    echo 'ERROR: UiAutomator apk could not be found!'
    exit 9
fi
