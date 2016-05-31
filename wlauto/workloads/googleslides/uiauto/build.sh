#!/bin/bash

# CD into build dir if possible - allows building from any directory
script_path='.'
if `readlink -f $0 &>/dev/null`; then
    script_path=`readlink -f $0 2>/dev/null`
fi
script_dir=`dirname $script_path`
cd $script_dir

# Ensure build.xml exists before starting
if [[ ! -f build.xml ]]; then
    echo 'Ant build.xml file not found! Check that you are in the right directory.'
    exit 9
fi

# Copy base classes from wlauto dist
class_dir=bin/classes/com/arm/wlauto/uiauto
base_classes=`python -c "import os, wlauto; print os.path.join(os.path.dirname(wlauto.__file__), 'common', 'android', '*.class')"`
mkdir -p $class_dir
cp $base_classes $class_dir

# Build and return appropriate exit code if failed
ant build
exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    echo "ERROR: 'ant build' exited with code $exit_code"
    exit $exit_code
fi

# If successful move JAR file to workload folder (remove previous)
package=com.arm.wlauto.uiauto.googleslides.jar
rm -f ../$package
if [[ -f bin/$package ]]; then
    cp bin/$package ..
else
    echo 'ERROR: UiAutomator JAR could not be found!'
    exit 9
fi
