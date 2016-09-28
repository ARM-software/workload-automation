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
    public String packageID;

    public static final String ACTION_VOICE = "voice";
    public static final String ACTION_VIDEO = "video";

    public void runUiAutomation() throws Exception {
        // Override superclass value
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(10);

        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";

        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");
        String contactName = parameters.getString("name").replace("0space0", " ");
        int callDuration = Integer.parseInt(parameters.getString("duration"));
        String callType = parameters.getString("action");
        String resultsFile = parameters.getString("results_file");

        setScreenOrientation(ScreenOrientation.NATURAL);

        UiWatcher infoPopUpWatcher = createInfoPopUpWatcher();
        registerWatcher("infoPopUpWatcher", infoPopUpWatcher);
        runWatchers();

        // Run tests
        handleLoginScreen(loginName, loginPass);
        dismissUpdatePopupIfPresent();
        searchForContact(contactName);

        if (ACTION_VOICE.equalsIgnoreCase(callType)) {
            voiceCallTest(callDuration);
        } else if (ACTION_VIDEO.equalsIgnoreCase(callType)) {
            videoCallTest(callDuration);
        }

        removeWatcher("infoPopUpWatcher");
        unsetScreenOrientation();
    }

    public void handleLoginScreen(String username, String password) throws Exception {
        UiObject useridField =
            new UiObject(new UiSelector().resourceId(packageID + "sign_in_userid"));
        UiObject nextButton =
            new UiObject(new UiSelector().resourceId(packageID + "sign_in_next_btn"));
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
        if (updateNotice.waitForExists(uiAutoTimeout)) {
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
        search.setText(name);

        UiObject peopleItem = clickUiObject(BY_TEXT, name, "android.widget.TextView");

        UiObject avatarPresence =
            new UiObject(new UiSelector().resourceId(packageID + "skype_avatar_presence"));

        UiObject confirm =
            new UiObject(new UiSelector().resourceId(packageID + "fab"));

        // On some devices two clicks are needed to select a contact.
        if (!avatarPresence.waitUntilGone(uiAutoTimeout)) {
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

    private void voiceCallTest(int duration) throws Exception {
        String testTag = "call_voice";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        logger.start();
        makeCall(duration, false, testTag);
        logger.stop();
    }

    private void videoCallTest(int duration) throws Exception {
        String testTag = "call_video";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        logger.start();
        makeCall(duration, true, testTag);
        logger.stop();
    }

    private void makeCall(int duration, boolean video, String testTag) throws Exception {
        String description = video ? "Video call" : "Call options";

        UiObject callButton =
            new UiObject(new UiSelector().descriptionContains(description));
        callButton.clickAndWaitForNewWindow();

        UiObject muteButton =
            new UiObject(new UiSelector().descriptionContains("Mute"));
        muteButton.click();
        
        sleep(duration);
    }
}
