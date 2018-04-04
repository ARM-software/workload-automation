/*    Copyright 2013-2015 ARM Limited
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


package com.arm.wa.uiauto.facebook;

import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;

import com.arm.wa.uiauto.BaseUiAutomation;

import static com.arm.wa.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "facebook";

    /*
     * The 'runWorkload' method implements the following activities
     * Login to facebook account.
     * Send a message.
     * Check latest notification.
     * Search particular user account and visit his/her facebook account.
     * Update the facebook status
     */
    @Test
    public void runWorkload() throws Exception {
        initialize_instrumentation();
        final int timeout = 4;
        UiSelector selector = new UiSelector();

        UiObject logInButton = mDevice.findObject(selector
             .className("android.widget.Button").index(3).text("Log In"));

        UiObject emailField = mDevice.findObject(selector
                                     .className("android.widget.EditText").index(1));
        emailField.clearTextField();
        emailField.setText("abkksathe@gmail.com");

        UiObject passwordField = mDevice.findObject(selector
                                        .className("android.widget.EditText").index(2));
        passwordField.clearTextField();
        passwordField.setText("highelymotivated");

        logInButton.clickAndWaitForNewWindow(timeout);

        sleep(timeout);

        //Click on message logo
        UiObject messageLogo = mDevice.findObject(new UiSelector()
             .className("android.widget.RelativeLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.LinearLayout").index(3)
             .childSelector(new UiSelector()
             .className("android.widget.RelativeLayout").index(1)
             .childSelector(new UiSelector()
             .className("android.widget.ImageButton").index(0)))));
        messageLogo.clickAndWaitForNewWindow(timeout);

        //send message
        UiObject clickMessage = mDevice.findObject(new UiSelector()
            .className("android.support.v4.view.ViewPager").index(0)
            .childSelector(new UiSelector()
            .className("android.widget.RelativeLayout").index(1)));
        clickMessage.clickAndWaitForNewWindow(timeout);

        sleep(timeout);

        UiObject sendMessage = mDevice.findObject(new UiSelector()
            .className("android.widget.FrameLayout").index(4)
            .childSelector(new UiSelector()
            .className("android.widget.LinearLayout").index(2))
            .childSelector(new UiSelector()
            .className("android.widget.EditText").index(0)
            .text("Write a message")));
        sendMessage.click();

        sleep(timeout);

        UiObject editMessage = mDevice.findObject(new UiSelector()
            .className("android.widget.EditText").text("Write a message"));

        editMessage.setText("Hi how are you?????");

        UiObject sendButton = mDevice.findObject(new UiSelector(
            ).resourceIdMatches(".*compose_button_send"));
        sendButton.click();

        mDevice.pressDPadDown();
        sleep(timeout);
        mDevice.pressBack();
        sleep(timeout);
        mDevice.pressBack();

        //Check for notifications
        UiObject clickNotificationsLogo = mDevice.findObject(new UiSelector()
             .className("android.widget.RelativeLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.LinearLayout").index(3)
             .childSelector(new UiSelector()
             .className("android.widget.RelativeLayout").index(2)
             .childSelector(new UiSelector()
             .className("android.widget.ImageButton").index(0)))));
        clickNotificationsLogo.clickAndWaitForNewWindow(timeout);

        //Click on a 'do you know' notification.
        UiObject clickNotify = mDevice.findObject(new UiSelector()
             .textContains("You have a new friend suggestion"));
        clickNotify.clickAndWaitForNewWindow(timeout);

        sleep(timeout);
        mDevice.pressBack();
        sleep(timeout);
        mDevice.pressBack();

        //Search for the facebook account
        UiObject clickBar = mDevice.findObject(new UiSelector()
             .className("android.widget.ImageButton").index(0)
             .description("Main navigation menu"));
        clickBar.clickAndWaitForNewWindow(timeout);

        UiObject clickSearch = mDevice.findObject(new UiSelector()
             .className("android.widget.FrameLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.LinearLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.FrameLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.FrameLayout").index(1)
             .childSelector(new UiSelector()
             .className("android.widget.EditText").index(1)
             .text("Search"))))));
        clickSearch.clickAndWaitForNewWindow(timeout);

        UiObject editSearch = getUiObjectByResourceId("com.facebook.katana:id/searchbox",
                                                      "android.widget.EditText");

        editSearch.clearTextField();
        typeText(editSearch, "amol kamble");
        sleep(timeout);

        clickUiObject(BY_DESC, "Amol Kamble", "android.view.View", true);
        sleep(timeout);

        mDevice.pressBack();
        sleep(timeout);
        mDevice.pressBack();

        sleep(timeout);

        //Click on find friends
        //Update the status
        UiObject updateStatus = getUiObjectByResourceId("com.facebook.katana:id/publisher_status");
        updateStatus.clickAndWaitForNewWindow(timeout);

        UiObject editUpdateStatus = mDevice.findObject(new UiSelector()
             .className("android.widget.EditText")
             .text("What's on your mind?"));
        editUpdateStatus.clearTextField();
        editUpdateStatus.setText("hellllooooooo its done!!");

        UiObject clickPost = mDevice.findObject(new UiSelector()
             .className("android.widget.RelativeLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.LinearLayout").index(3)));
        clickPost.clickAndWaitForNewWindow(timeout);

        sleep(2 * timeout);
        mDevice.pressHome();
    }

    // Simulate typing speed for fields that get updated in real time (like search boxes)
    private void typeText(UiObject textObj, String text) throws UiObjectNotFoundException {
        for (int i = 1; i <= text.length(); i++) {
            textObj.setText(text.substring(0, i));
            // Sleep is not needed for fields that get updated in real time.
            // You get about typing speed.
        }
    }
}
