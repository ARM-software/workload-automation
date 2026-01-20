/*    Copyright 2014-2018 ARM Limited
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

package com.arm.wa.uiauto.applaunch;

import android.os.Build;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.util.Log;

import com.arm.wa.uiauto.ApplaunchInterface;
import com.arm.wa.uiauto.BaseUiAutomation;
import com.arm.wa.uiauto.UxPerfUiAutomation;
import com.arm.wa.uiauto.ActionLogger;


import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.File;
import java.io.InputStreamReader;

import dalvik.system.DexClassLoader;


@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {
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

    protected Bundle parameters;
    protected String packageName;
    protected String packageID;
    protected boolean suHasCommandOption;

    @Before
    public void initialize() throws Exception {
        parameters = getParams();
        packageID = getPackageID(parameters);

        suHasCommandOption = parameters.getBoolean("su_has_command_option");

        // Get workload apk file parameters
        packageName = parameters.getString("package_name");
        String workload = parameters.getString("workload");
        String workloadAPKFile = parameters.getString("workload_apk");

        // Load the apk file
        File apkFile = new File(workloadAPKFile);
        File dexLocation = mContext.getDir("outdex", 0);
        if(!apkFile.exists()) {
            throw new Exception(String.format("APK file not found: %s ", workloadAPKFile));
        }
        DexClassLoader classloader = new DexClassLoader(apkFile.toURI().toURL().toString(),
                                                        dexLocation.getAbsolutePath(),
                                                        null, mContext.getClassLoader());

        Class uiautomation = null;
        Object uiautomation_interface = null;
        String workloadClass = String.format("com.arm.wa.uiauto.%1s.UiAutomation", workload);
        try {
            uiautomation = classloader.loadClass(workloadClass);
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }

        Log.d("Class loaded:", uiautomation.getCanonicalName());
        uiautomation_interface = uiautomation.newInstance();

        // Create an Application Interface object from the workload
        launch_workload = ((ApplaunchInterface)uiautomation_interface);
        launch_workload.initialize_instrumentation();
        launch_workload.setWorkloadParameters(parameters);

        // Get parameters for application launch
        applaunchType = parameters.getString("applaunch_type");
        applaunchIterations = parameters.getInt("applaunch_iterations");
        activityName = parameters.getString("launch_activity");
    }

    /**
     * Setup run for applaunch workload that clears the initial
     * run dialogues on launching an application package.
     */
    @Test
    public void setup() throws Exception {
        mDevice.setOrientationNatural();
        launch_workload.runApplicationSetup();
        unsetScreenOrientation();
        closeApplication();
    }

    @Test
    public void runWorkload() throws Exception {
        launchEndObject = launch_workload.getLaunchEndObject();
        for (int iteration = 0; iteration < applaunchIterations; iteration++) {
            Log.d("Applaunch iteration number: ", String.valueOf(applaunchIterations));
            sleep(20);//sleep for a while before next iteration
            killBackground();
            runApplaunchIteration(iteration);
            closeApplication();
        }
    }

    @Test
    public void teardown() throws Exception {
        mDevice.unfreezeRotation();
    }

    /**
     * This method performs multiple iterations of application launch and
     * records the time taken for each iteration.
     */
    public void runApplaunchIteration(Integer iteration_count) throws Exception{
        String testTag = "applaunch" + iteration_count;
        String launchCommand = launch_workload.getLaunchCommand();
        AppLaunch applaunch = new AppLaunch(testTag, launchCommand);
        applaunch.startLaunch();  // Launch the application and start timer
        applaunch.endLaunch();  // marks the end of launch and stops timer
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

        public AppLaunch(String testTag, String launchCommand) {
            this.testTag = testTag;
            this.launchCommand = launchCommand;
            this.logger = new ActionLogger(testTag, parameters);
        }

        // Beginning of application launch
        public void startLaunch() throws Exception{
            logger.start();
            launchMain();
        }

        // Launches the application.
        public void launchMain() throws Exception{
            executeShellCommand(launchCommand);
        }

        // Marks the end of application launch of the workload.
        public void endLaunch() throws Exception{
            waitObject(launchEndObject, launch_timeout);
            logger.stop();
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
        String command = String.format("am force-stop %s", packageName);
        executeShellCommand(command);
    }

    // Kills the background processes
    public void killBackground() throws Exception{
        // Workload has KILL_BACKGROUND_PROCESSES permission so it can execute following
        // command and it is not necessary to execute it with shell permissions.
        Process kill_p;
        kill_p = Runtime.getRuntime().exec("am kill-all");
        kill_p.waitFor();
        kill_p.destroy();
    }

    // Drop the caches
    public void dropCaches() throws Exception{
        executeShellCommand("sync", /*asRoot=*/true);
        executeShellCommand("echo 3 > /proc/sys/vm/drop_caches", /*asRoot=*/true);
    }

    private String getSuCommand(String command) {
        if (suHasCommandOption) {
            return String.format("su -c '%s'", command);
        }
        // If su doesn't support -c argument we assume that it has following usage:
        //   su [WHO [COMMAND]]
        // that corresponds to su from engineering Android version.
        return String.format("su root %s", command);
    }

    private void executeShellCommand(String command) throws Exception {
        executeShellCommand(command, /*asRoot=*/false);
    }

    private static ParcelFileDescriptor[] executeShellCommand(android.app.UiAutomation uiAutomation,
                                                              String command) throws IOException {
        ParcelFileDescriptor[] result = new ParcelFileDescriptor[2];
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            ParcelFileDescriptor[] fds = uiAutomation.executeShellCommandRwe(command);
            fds[1].close(); // close stdin
            result[0] = fds[0]; // stdout
            result[1] = fds[2]; // stderr
            return result;
        }

        result[0] = uiAutomation.executeShellCommand(command);
        return result;
    }

    private void executeShellCommand(String command, boolean asRoot) throws Exception {
        android.app.UiAutomation uiAutomation = mInstrumentation.getUiAutomation();

        String shellCommand = command;
        if (asRoot) {
            shellCommand = getSuCommand(command);
        }

        Log.d("Shell command: ", shellCommand);
        ParcelFileDescriptor[] fds = UiAutomation.executeShellCommand(uiAutomation, command);
        ParcelFileDescriptor fdOut = fds[0];
        ParcelFileDescriptor fdErr = fds[1];

        String out = readStreamAndClose(fdOut);
        Log.d("Shell out: ", out);

        String err = readStreamAndClose(fdErr);
        if (!err.isEmpty()) {
            Log.e("Shell err: ", err);
            String msg = String.format("Shell command '%s' failed with error: '%s'", command, err);
            throw new Exception(msg);
        }
    }

    private static String readStreamAndClose(ParcelFileDescriptor fd) throws IOException {
        if (fd == null) {
            return "";
        }

        try (BufferedReader in = new BufferedReader(new InputStreamReader(
                new ParcelFileDescriptor.AutoCloseInputStream(fd)))) {
            StringBuilder sb = new StringBuilder();
            while (true) {
                String line = in.readLine();
                if (line == null) {
                    break;
                }
                sb.append(line);
                sb.append('\n');
            }
            return sb.toString();
        }
    }
}
