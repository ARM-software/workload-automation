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

import java.util.concurrent.TimeUnit;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String ACTION_VOICE = "voice";
    public static final String ACTION_VIDEO = "video";

    public Bundle parameters;
    public String packageName;
    public String packageID;

    public void runUiAutomation() throws Exception {
        // Override superclass value
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(10);

        // Get Params
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
        String useridResoureId = packageID + "sign_in_userid";
        String nextButtonResourceId = packageID + "sign_in_next_btn";
        UiObject useridField = new UiObject(new UiSelector().resourceId(useridResoureId));
        UiObject nextButton = new UiObject(new UiSelector().resourceId(nextButtonResourceId));
        useridField.setText(username);
        nextButton.clickAndWaitForNewWindow();

        String passwordResoureId = packageID + "signin_password";
        String signinButtonResourceId = packageID + "sign_in_btn";
        UiObject passwordField = new UiObject(new UiSelector().resourceId(passwordResoureId));
        UiObject signinButton = new UiObject(new UiSelector().resourceId(signinButtonResourceId));
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

            UiObject contiuneButton = getUiObjectByText("Continue", "android.widget.Button");
            if (contiuneButton.exists()) {
                contiuneButton.click();
            }
        }
    }

    public void searchForContact(String name) throws Exception {
        UiObject menuSearch = new UiObject(new UiSelector().resourceId(packageID + "menu_search"));
        boolean sharingResource = false;

        // If searching for a contact from Skype directly we need
        // to click the menu search button to display the contact search box.
        if (menuSearch.waitForExists(uiAutoTimeout)) {
            menuSearch.click();

        // If sharing a resource from another app the contact search box is shown
        // by default.
        } else {
            sharingResource = true;
        }

        UiObject search = getUiObjectByText("Search", "android.widget.EditText");
        search.setText(name);

        UiObject peopleItem = getUiObjectByText(name, "android.widget.TextView");

        peopleItem.waitForExists(uiAutoTimeout);
        peopleItem.click();

        UiObject avatarPresence =
            new UiObject(new UiSelector().resourceId(packageID + "skype_avatar_presence"));

        // On some devices two clicks are needed to select a contact.
        if (!avatarPresence.waitUntilGone(uiAutoTimeout)) {
            peopleItem.click();
        }

        // Before sharing a resource from another app we first need to
        // confirm our selection.
        if (sharingResource) {
            UiObject confirm =
                new UiObject(new UiSelector().resourceId(packageID + "fab"));
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

                    Long viewTimeout = TimeUnit.SECONDS.toMillis(10);
                    boolean dismissed = dismissButton.waitUntilGone(viewTimeout);

                    return dismissed;
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

        UiObject callButton = new UiObject(new UiSelector().descriptionContains(description));
        callButton.clickAndWaitForNewWindow();

        UiObject muteButton = new UiObject(new UiSelector().descriptionContains("Mute"));
        muteButton.click();
        sleep(duration);
    }
}
