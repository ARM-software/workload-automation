/*    Copyright 2014-2016 ARM Limited
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

package com.arm.wlauto.uiauto.applaunch;

import android.os.Bundle;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.ApplaunchInterface;
import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

import java.util.concurrent.TimeUnit;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.Map.Entry;
import dalvik.system.DexClassLoader;
import java.lang.reflect.Method;


public class UiAutomation extends UxPerfUiAutomation {

    /** 
     * Uiobject that marks the end of launch of an application, which is workload
     * specific and added in the workload Java file by a method called getLaunchEndObject().
     */
    public UiObject launchEndObject;
    /** Timeout to wait for application launch to finish. */
    private Integer launch_timeout = 10;
    public String applaunchType;
    public int applaunchIterations;
    public String activityName;
    public ApplaunchInterface launch_workload;

    /** Uiautomator function called by the applaunch workload. */
    public void runUiAutomation() throws Exception{
        parameters = getParams();

        // Get workload jar file parameters
        String workload = parameters.getString("workload");
        String binariesDirectory = parameters.getString("binaries_directory");
        String workloadJarPath = parameters.getString("workdir");
        String workloadJarName = String.format("com.arm.wlauto.uiauto.%1s.jar",workload);
        String workloadJarFile = String.format("%1s/%2s",workloadJarPath, workloadJarName);

        // Load the jar file
        File jarFile = new File(workloadJarFile);
        if(!jarFile.exists()) {
            throw new Exception(String.format("Jar file not found: %s", workloadJarFile));
        }
        DexClassLoader classloader = new DexClassLoader(jarFile.toURI().toURL().toString(),
                                     binariesDirectory, null, ClassLoader.getSystemClassLoader());
        Class uiautomation = null;
        Object uiautomation_interface = null;
        String workloadClass = String.format("com.arm.wlauto.uiauto.%1s.UiAutomation",workload);
        try {
            uiautomation = classloader.loadClass(workloadClass);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
        Log.d("Class loaded:", uiautomation.getCanonicalName());
        uiautomation_interface = uiautomation.newInstance();

        // Create an Application Interface object from the workload
        launch_workload = ((ApplaunchInterface)uiautomation_interface);

        // Get parameters for application launch
        getPackageParameters();
        applaunchType = parameters.getString("applaunch_type");
        applaunchIterations = parameters.getInt("applaunch_iterations");
        activityName = parameters.getString("launch_activity");

        // Run the workload for application launch initialization
        runApplaunchSetup();

        // Run the workload for application launch measurement
        for (int iteration = 0; iteration < applaunchIterations; iteration++) {
            Log.d("Applaunch iteration number: ", String.valueOf(applaunchIterations));
            sleep(20);//sleep for a while before next iteration
            killBackground();
            runApplaunchIteration(iteration);
            closeApplication();
        }
    }

    /**
     * Setup run for applaunch workload that clears the initial
     * run dialogues on launching an application package.
     */
    public void runApplaunchSetup() throws Exception{
        setScreenOrientation(ScreenOrientation.NATURAL);
        launch_workload.setWorkloadParameters(parameters);
        launch_workload.runApplicationInitialization();
        launchEndObject = launch_workload.getLaunchEndObject();
        unsetScreenOrientation();
        closeApplication();
    }

    /**
     * This method performs multiple iterations of application launch and
     * records the time taken for each iteration.
     */
    public void runApplaunchIteration(Integer iteration_count) throws Exception{
        String testTag = "applaunch" + iteration_count;
        String launchCommand = launch_workload.getLaunchCommand();
        AppLaunch applaunch = new AppLaunch(testTag, launchCommand);
        applaunch.startLaunch();//Launch the application and start timer
        applaunch.endLaunch();//marks the end of launch and stops timer
    }

    /*
     * AppLaunch class implements methods that facilitates launching applications
     * from the uiautomator. It has methods that are used for one complete iteration of application
     * launch instrumentation.
     * ActionLogger class is instantiated within the class for measuring applaunch time.
     * startLaunch(): Marks the beginning of the application launch, starts Timer
     * endLaunch(): Marks the end of application, ends Timer
     * launchMain(): Starts the application launch process and validates the finish of launch.
    */
    private class AppLaunch {

        private String testTag;
        private String launchCommand;
        private ActionLogger logger;
        Process launch_p;

        public AppLaunch(String testTag, String launchCommand) {
            this.testTag = testTag;
            this.launchCommand = launchCommand;
            this.logger = new ActionLogger(testTag, parameters);
        }

        // Called by launchMain() to check if app launch is successful
        public void launchValidate(Process launch_p) throws Exception {
            launch_p.waitFor();
            Integer exit_val = launch_p.exitValue();
            if (exit_val != 0) {
                throw new Exception("Application could not be launched");
            }
        }

        // Marks the end of application launch of the workload.
        public void endLaunch() throws Exception{
            waitObject(launchEndObject, launch_timeout);
            logger.stop();
            launch_p.destroy();
        }

        // Launches the application.
        public void launchMain() throws Exception{
            launch_p = Runtime.getRuntime().exec(launchCommand);

            launchValidate(launch_p);
        }

        // Beginning of application launch
        public void startLaunch() throws Exception{
            logger.start();
            launchMain();
        }
    }

    // Exits the application according to application launch type.
    public void closeApplication() throws Exception{
        if(applaunchType.equals("launch_from_background")) {
            pressHome();
        }
        else if(applaunchType.equals("launch_from_long-idle")) {
            killApplication();
            dropCaches();
        }
    }

    // Kills the application process
    public void killApplication() throws Exception{
        Process kill_p;
        kill_p = Runtime.getRuntime().exec(String.format("am force-stop %s", packageName));
        kill_p.waitFor();
        kill_p.destroy();
    }

    // Kills the background processes
    public void killBackground() throws Exception{
        Process kill_p;
        kill_p = Runtime.getRuntime().exec("am kill-all");
        kill_p.waitFor();
        kill_p.destroy();
    }

    // Drop the caches
    public void dropCaches() throws Exception{
        Process drop_cache;
        drop_cache = Runtime.getRuntime().exec("su sync; su echo 3 > /proc/sys/vm/drop_caches");
        drop_cache.waitFor();
        drop_cache.destroy();
    }
}
