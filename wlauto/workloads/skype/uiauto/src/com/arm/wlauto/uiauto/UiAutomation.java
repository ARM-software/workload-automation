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

package com.arm.wlauto.uiauto.skype;

import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.core.UiWatcher;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

import java.util.concurrent.TimeUnit;

public class UiAutomation extends UxPerfUiAutomation {

    public Bundle parameters;
    public String packageName;
    protected String activityName;
    protected String applaunchType;
    public String packageID;

    public static final String ACTION_VOICE = "voice";
    public static final String ACTION_VIDEO = "video";

    public void runUiAutomation() throws Exception {
        // Override superclass value
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(10);

        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";

        String contactName = parameters.getString("name").replace("0space0", " ");
        int callDuration = Integer.parseInt(parameters.getString("duration"));
        String callType = parameters.getString("action");
        String resultsFile = parameters.getString("results_file");

        setScreenOrientation(ScreenOrientation.NATURAL);

        UiWatcher infoPopUpWatcher = createInfoPopUpWatcher();
        registerWatcher("infoPopUpWatcher", infoPopUpWatcher);
        runWatchers();

        // Run tests
        clearDialogues();
        searchForContact(contactName);

        if (ACTION_VOICE.equalsIgnoreCase(callType)) {
            makeCall(callDuration, false);
        } else if (ACTION_VIDEO.equalsIgnoreCase(callType)) {
            makeCall(callDuration, true);
        }

        removeWatcher("infoPopUpWatcher");
        unsetScreenOrientation();
    }
    
    public void clearDialogues() throws Exception {
        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");
        handleLoginScreen(loginName, loginPass);
        dismissUpdatePopupIfPresent();
    }

    public void applaunchEnd() throws Exception {
        applaunchType = parameters.getString("applaunch_type");
        if (applaunchType.equals("launch_from_background")) {
            pressHome();
        }
    }
    
    public void runApplaunchSetup() throws Exception {
        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";
        sleep(5);
        setScreenOrientation(ScreenOrientation.NATURAL);
        clearDialogues();
        unsetScreenOrientation();
        applaunchEnd();
    }
    
    public void runApplaunchIteration() throws Exception {
        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";
        activityName = parameters.getString("launch_activity");
        String actionName = "android.intent.action.VIEW"; //required for launching skype
        String dataURI = "skype:dummy?dummy"; // required for launching skype

        String iteration_count = parameters.getString("iteration_count");
        String testTag = "applaunch" + iteration_count;
        //Applaunch object for launching an application and measuring the time taken
        AppLaunch applaunch = new AppLaunch(testTag, packageName, activityName, parameters);
        //Widget on the screen that marks the application ready for user interaction
        UiObject userBeginObject =
            new UiObject(new UiSelector().resourceId(packageID + "menu_search"));
        
        UiWatcher videoPopupWatcher = videoPopupWatcher();
        registerWatcher("videoPopupwatcher", videoPopupWatcher);
        runWatchers();

        applaunch.startLaunch(actionName, dataURI);//Launch the appl;ication and start timer 
        applaunch.endLaunch(userBeginObject,10);//marks the end of launch and stops timer
        applaunchEnd();

    }

    public void handleLoginScreen(String username, String password) throws Exception {
        UiObject useridField =
            new UiObject(new UiSelector().resourceId(packageID + "sign_in_userid"));
        UiObject nextButton =
            new UiObject(new UiSelector().resourceId(packageID + "sign_in_next_btn"));

        // Wait for login screen to appear
        waitObject(useridField, 20);

        useridField.setText(username);
        nextButton.clickAndWaitForNewWindow();

        UiObject passwordField =
            new UiObject(new UiSelector().resourceId(packageID + "signin_password"));
        UiObject signinButton =
            new UiObject(new UiSelector().resourceId(packageID + "sign_in_btn"));
        passwordField.setText(password);
        signinButton.clickAndWaitForNewWindow();
    }

    public void dismissUpdatePopupIfPresent() throws Exception {
        UiObject updateNotice =
            new UiObject(new UiSelector().resourceId(packageID + "update_notice_dont_show_again"));
        //Detect if the update notice popup is present
        if (updateNotice.waitForExists(TimeUnit.SECONDS.toMillis(30))) {
            //Stop the notice from reappearing
            updateNotice.click();
            clickUiObject(BY_TEXT, "Continue", "android.widget.Button");
        }
    }

    public void searchForContact(String name) throws Exception {
        boolean sharingResource = false;
        UiObject menuSearch =
            new UiObject(new UiSelector().resourceId(packageID + "menu_search"));
        if (menuSearch.waitForExists(uiAutoTimeout)) {
            // If searching for a contact from Skype directly we need
            // to click the menu search button to display the contact search box.
            menuSearch.click();
        } else {
            // If sharing a resource from another app the contact search box is shown
            // by default.
            sharingResource = true;
        }

        UiObject search = getUiObjectByText("Search", "android.widget.EditText");
        // Wait for search screen to appear
        waitObject(search, 10);
        search.setText(name);

        UiObject peopleItem = new UiObject(new UiSelector().textContains(name)
                                           .resourceId(packageID + "people_item_full_name"));
        peopleItem.click();

        UiObject search_item_icon =
            new UiObject(new UiSelector().resourceId(packageID + "search_item_icon"));

        UiObject confirm =
            new UiObject(new UiSelector().resourceId(packageID + "fab"));

        // On some devices two clicks are needed to select a contact.
        if (!search_item_icon.waitUntilGone(uiAutoTimeout)) {
            if (!sharingResource || !confirm.exists()) {
                peopleItem.click();
            }
        }

        // Before sharing a resource from another app we first need to
        // confirm our selection.
        if (sharingResource) {
            confirm.click();
        }
    }

    // Creates a watcher for when a pop up dialog appears with a dismiss button.
    private UiWatcher videoPopupWatcher() throws Exception {
        UiWatcher infoPopUpWatcher = new UiWatcher() {
            @Override
            public boolean checkForCondition() {
                UiObject gotitButton =
                    new UiObject(new UiSelector().textContains("GOT IT"));

                if (gotitButton.exists()) {
                    try {
                        gotitButton.click();
                    } catch (UiObjectNotFoundException e) {
                        e.printStackTrace();
                    }

                    return gotitButton.waitUntilGone(TimeUnit.SECONDS.toMillis(10));
                }
                return false;
            }
        };
        return infoPopUpWatcher;
    }
    // Creates a watcher for when a pop up dialog appears with a dismiss button.
    private UiWatcher createInfoPopUpWatcher() throws Exception {
        UiWatcher infoPopUpWatcher = new UiWatcher() {
            @Override
            public boolean checkForCondition() {
                UiObject dismissButton =
                    new UiObject(new UiSelector().resourceId(packageID + "dismiss_button"));

                if (dismissButton.exists()) {
                    try {
                        dismissButton.click();
                    } catch (UiObjectNotFoundException e) {
                        e.printStackTrace();
                    }

                    return dismissButton.waitUntilGone(TimeUnit.SECONDS.toMillis(10));
                }
                return false;
            }
        };
        return infoPopUpWatcher;
    }

    private void makeCall(int duration, boolean video) throws Exception {
        String testTag = video ? "video" : "voice";
        String description = video ? "Video call" : "Call options";

        UiObject callButton =
            new UiObject(new UiSelector().descriptionContains(description));
        UiObject muteButton =
            new UiObject(new UiSelector().descriptionContains("mute"));
        UiObject endButton =
            new UiObject(new UiSelector().descriptionContains("end"));

        // Start the call and log how long that takes
        ActionLogger logger = new ActionLogger(testTag + "_start", parameters);
        logger.start();
        long target = System.currentTimeMillis() + TimeUnit.SECONDS.toMillis(duration);
        callButton.clickAndWaitForNewWindow();
        logger.stop();

        // Wait for 'duration' seconds - attempt to mute while waiting
        logger = new ActionLogger(testTag + "_call", parameters);
        logger.start();
        boolean muted = false;
        while (System.currentTimeMillis() < target) {
            if (muted == true) {
                sleep(1);
            } else {
                muted = tryButton(muteButton, 500);
            }
        }
        logger.stop();

        // Hang up the call and log how long that takes
        logger = new ActionLogger(testTag + "_stop", parameters);
        logger.start();
        if (!(tryButton(endButton, 500))){
            throw new UiObjectNotFoundException("Could not find end call button on screen.");
        }
        logger.stop();
    }

    private boolean tryButton(UiObject button, long timeout) throws Exception {
        if (button.waitForExists(timeout)) {
            button.click();
            return true;
        }
        else {
            // The buttons could be hidden...
            // Tap screen to make them appear and look again
            tapDisplayCentre();
            if (button.waitForExists(timeout)) {
                button.click();
                return true;
            }
        }
        return false;
    }
}
