package com.arm.wlauto.uiauto.skype;

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

import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiWatcher;

import com.arm.wlauto.uiauto.ApplaunchInterface;
import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends UxPerfUiAutomation implements ApplaunchInterface {

    public static final String ACTION_VOICE = "voice";
    public static final String ACTION_VIDEO = "video";

    @Test
    public void runUiAutomation() throws Exception {

        // Override superclass value
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(10);

        initialize_instrumentation();
        parameters = getParams();

        String contactName = parameters.getString("name");
        int callDuration = parameters.getInt("duration");
        String callType = parameters.getString("action");
        String resultsFile = parameters.getString("results_file");

        setScreenOrientation(ScreenOrientation.NATURAL);
        runApplicationInitialization();

        searchForContact(contactName);

        if (ACTION_VOICE.equalsIgnoreCase(callType)) {
            makeCall(callDuration, false);
        } else if (ACTION_VIDEO.equalsIgnoreCase(callType)) {
            makeCall(callDuration, true);
        }

        removeWatcher("infoPopUpWatcher");
        unsetScreenOrientation();
    }

    // Get application parameters and clear the initial run dialogues of the application launch.
    public void runApplicationInitialization() throws Exception {
        getPackageParameters();
        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");

        UiWatcher infoPopUpWatcher = createInfoPopUpWatcher();
        registerWatcher("infoPopUpWatcher", infoPopUpWatcher);
        UiWatcher nextPopUpWatcher = createNextPopUpWatcher();
        registerWatcher("nextPopUpWatcher", nextPopUpWatcher);
        runWatchers();

        // Run tests
        handleLoginScreen(loginName, loginPass);
        dismissUpdatePopupIfPresent();
    }

    // Sets the UiObject that marks the end of the application launch.
    public UiObject getLaunchEndObject() {
        UiObject launchEndObject = mDevice.findObject(new UiSelector()
                .resourceId(packageID + "menu_search"));
        return launchEndObject;
    }

    // Returns the launch command for the application.
    public String getLaunchCommand() {
        String launch_command;
        String actionName = "android.intent.action.VIEW";
        String dataURI = "skype:dummy?dummy";
        launch_command = String.format("am start --user -3 -a %s -d %s", actionName, dataURI);
        return launch_command;
    }

    // Pass the workload parameters, used for applaunch
    public void setWorkloadParameters(Bundle workload_parameters) {
        parameters = workload_parameters;
    }

    public void handleLoginScreen(String username, String password) throws Exception {
        UiObject useridField =
                mDevice.findObject(new UiSelector().resourceId(packageID + "sign_in_userid"));
        UiObject nextButton =
                mDevice.findObject(new UiSelector().resourceId(packageID + "sign_in_next_btn"));

        // Wait for login screen to appear
        waitObject(useridField, 20);

        useridField.setText(username);
        nextButton.clickAndWaitForNewWindow();

        UiObject passwordField =
                mDevice.findObject(new UiSelector().resourceId(packageID + "signin_password"));
        UiObject signinButton =
                mDevice.findObject(new UiSelector().resourceId(packageID + "sign_in_btn"));
        passwordField.setText(password);
        signinButton.clickAndWaitForNewWindow();
    }

    public void dismissUpdatePopupIfPresent() throws Exception {
        UiObject updateNotice =
                mDevice.findObject(new UiSelector().resourceId(packageID + "update_notice_dont_show_again"));
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
                mDevice.findObject(new UiSelector().resourceId(packageID + "menu_search"));
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

        UiObject peopleItem = mDevice.findObject(new UiSelector().textContains(name)
                .resourceId(packageID + "people_item_full_name"));
        UiObject search_item_icon =
                mDevice.findObject(new UiSelector().resourceId(packageID + "search_item_icon"));
        UiObject confirm =
                mDevice.findObject(new UiSelector().resourceId(packageID + "fab"));

        peopleItem.click();

        if (!sharingResource){
            // On some devices two clicks are needed to select a contact.
            if (!search_item_icon.waitUntilGone(uiAutoTimeout)) {
                if (!sharingResource || !confirm.exists()) {
                    peopleItem.click();
                }
            }
        }

        // Before sharing a resource from another app we first need to
        // confirm our selection.
        if (sharingResource) {
            confirm.click();
        }
    }

    // Creates a watcher for when a pop up dialog appears with a dismiss button.
    private UiWatcher createInfoPopUpWatcher() throws Exception {
        UiWatcher infoPopUpWatcher = new UiWatcher() {
            @Override
            public boolean checkForCondition() {
                UiObject dismissButton =
                        mDevice.findObject(new UiSelector().resourceId(packageID + "dismiss_button"));

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

    // Creates a watcher for when a pop up dialog appears with a next button on subsequent launch.
    private UiWatcher createNextPopUpWatcher() throws Exception {
        UiWatcher nextPopUpWatcher = new UiWatcher() {
            @Override
            public boolean checkForCondition() {
                UiObject nextButton =
                        mDevice.findObject(new UiSelector().resourceId(packageID + "next_button"));

                if (nextButton.exists()) {
                    pressBack();
                    return nextButton.waitUntilGone(TimeUnit.SECONDS.toMillis(100));
                }
                return false;
            }
        };
        return nextPopUpWatcher;
    }

    private void makeCall(int duration, boolean video) throws Exception {
        String testTag = video ? "video" : "voice";
        String description = video ? "Video call" : "Call options";

        UiObject callButton =
                mDevice.findObject(new UiSelector().descriptionContains(description));
        UiObject muteButton =
                mDevice.findObject(new UiSelector().descriptionContains("mute"));
        UiObject endButton =
                mDevice.findObject(new UiSelector().descriptionMatches("Hang [uU]p|End call"));

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
        if (!(tryButton(endButton))){
            throw new UiObjectNotFoundException("Could not find end call button on screen.");
        }
        logger.stop();
    }

    private boolean tryButton(UiObject button) throws Exception {
        return tryButton(button, uiAutoTimeout);
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
