/*    Copyright 2013-2016 ARM Limited
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

package com.arm.wlauto.uiauto;

import android.os.Bundle;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.core.UiWatcher;

public class UxPerfApplaunch extends BaseUiAutomation {
    public Bundle parameters;
    public String packageName;
    public String packageID;
    public String applaunchType;
    public String activityName;

	//Uiobject that marks the end of launch of an application.
	//This is workload spefific and added in the workload Java file
	//by a method called setUserBeginObject().
	public UiObject userBeginObject;

    //Timeout to wait for application launch to finish. 
	private Integer launch_timeout = 10;
	
	//Get application package parameter and create package ID
	public void getParameters() {
        parameters = getParams();
        packageName = parameters.getString("package");
        activityName = parameters.getString("launch_activity");
        packageID = packageName + ":id/";

	}
    
	//uiautomator function called by the uxperfapplaunch workload.
	public void runUxperfApplaunch() throws Exception {
        getParameters();
        applaunchType = parameters.getString("applaunch_type");
        String applaunchIterations = parameters.getString("applaunch_iterations");
        Log.d("Applaunch iteration number: ", applaunchIterations);
		runApplaunchSetup();
		for (int i = 0; i < Integer.parseInt(applaunchIterations); i++) {
			sleep(20);
			killBackground();
			runApplaunchIteration(i);
			closeApplication();
		}
	}
    

    //Setup run for uxperfapplaunch workload that clears the initial
	//run dialogues on launching an application package.
    public void runApplaunchSetup() throws Exception {
        sleep(5);
        setScreenOrientation(ScreenOrientation.NATURAL);
        clearDialogues();
		setUserBeginObject();
        unsetScreenOrientation();
        closeApplication();
	}
    
	//This method performs multiple iterations of application launch and 
	//records the time taken for each iteration.
	public void runApplaunchIteration(Integer iteration_count) throws Exception {
		String testTag = "applaunch" + iteration_count;
        AppLaunch applaunch = new AppLaunch(testTag);
        applaunch.startLaunch();//Launch the application and start timer 
        applaunch.endLaunch();//marks the end of launch and stops timer
    }
    
    /*
     * AppLaunch class implements methods that facilitates launching applications
	 * from the uiautomator.
     * ActionLogger class is instantiated within the class for measuring applaunch time.
     * startLaunch(): Marks the beginning of the application launch, starts Timer
     * endLaunch(): Marks the end of application, ends Timer
	 * launchMain(): Starts the application launch process and validates the finish of launch.
    */
    public class AppLaunch {

    	private String testTag;
        private ActionLogger logger;
        Process launch_p;

        public AppLaunch(String testTag) {
            this.testTag= testTag;
            this.logger = new ActionLogger(testTag, parameters);
        }
        
        
        //Called by launchMain() to check if app launch is successful
        public void launchValidate(Process launch_p) throws Exception {
            launch_p.waitFor();
            Integer exit_val = launch_p.exitValue();
            if (exit_val != 0) {
                throw new Exception("Application could not be launched");
            }
        }

        //Marks the end of application launch of the workload.
        public void endLaunch() throws Exception{
            waitObject(userBeginObject, launch_timeout);
            logger.stop();
            launch_p.destroy();
        }


        //Launches the application.
        public void launchMain() throws Exception{
            if(activityName.equals("None")) {
                launch_p = Runtime.getRuntime().exec(String.format("am start %s",
                                packageName));
            }
            else {
                launch_p = Runtime.getRuntime().exec(String.format("am start -n %s/%s",
                                packageName, activityName));
            }

            launchValidate(launch_p);

        }
        //Launches the application
        public void launchMain(String actionName, String dataURI) throws Exception{
            launch_p = Runtime.getRuntime().exec(String.format("am start -a %s -d %s",
                                actionName, dataURI));

            launchValidate(launch_p);
        }
        
        
        //Beginning of application launch
        public void startLaunch() throws Exception{
            logger.start();
            launchMain();
        }
        
		//Beginning of application launch
        public void startLaunch(String actionName, String dataURI) throws Exception{
            logger.start();
            launchMain(actionName, dataURI);
        }
    }
	
	//This method has the Uiautomation methods for clearing the initial run
	//dialogues of an application package. This is workload specific and 
	//is expected to be overridden by the workload that inherits this class.
    public void clearDialogues() throws Exception {

	}
    
	//Method that sets the userbeginObject per workload. This is workload specific and 
	//is expected to be overridden by the workload that inherits this class.
    public void setUserBeginObject() throws Exception {
	
	}

    //Exits the application according to application launch type.
    public void closeApplication() throws Exception{
        if(applaunchType.equals("launch_from_background")) {
            pressHome();
        }
        else if(applaunchType.equals("launch_from_long-idle")) {
            killApplication();
			dropCaches();
        }
    }
 
    //Kills the application process
    public void killApplication() throws Exception{
		Process kill_p;
		kill_p = Runtime.getRuntime().exec(String.format("am force-stop %s",packageName));
		kill_p.waitFor();
		kill_p.destroy();
    }
 
    //Kills the background processes
    public void killBackground() throws Exception{
		Process kill_p;
		kill_p = Runtime.getRuntime().exec("am kill-all");
		kill_p.waitFor();
		kill_p.destroy();
    }
    

	//Drop the caches
    public void dropCaches() throws Exception{
        Process drop_cache;
        drop_cache = Runtime.getRuntime().exec("sync; su echo 3 > /proc/sys/vm/drop_caches");
        drop_cache.waitFor();
        drop_cache.destroy();
    }

}
