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


package com.arm.wlauto.uiauto.facebook;

import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "facebook";

    /*
     * The 'runUiAutomation' method implements the following activities
     * Login to facebook account.
     * Send a message.
     * Check latest notification.
     * Search particular user account and visit his/her facebook account.
     * Go to find friends.
     * Update the facebook status
     */
@Test
public void runUiAutomation() throws Exception {
        initialize_instrumentation();
        final int timeout = 5;
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

        UiObject editSearch = mDevice.findObject(new UiSelector()
             .className("android.widget.EditText").index(0).text("Search"));

        editSearch.clearTextField();
        editSearch.setText("amol kamble");
        sleep(timeout);

        UiObject clickOnSearchResult = mDevice.findObject(new UiSelector()
             .className("android.webkit.WebView").index(0));
        clickOnSearchResult.clickTopLeft();

        sleep(2 * timeout);

        mDevice.pressBack();
        sleep(timeout);
        mDevice.pressBack();

        clickBar.click();

        sleep(timeout);

        //Click on find friends
        UiObject clickFriends = mDevice.findObject(new UiSelector()
             .className("android.widget.FrameLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.LinearLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.FrameLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.FrameLayout").index(1)
             .childSelector(new UiSelector()
             .className("android.widget.RelativeLayout").index(0)
             .childSelector(new UiSelector()
             .className("android.widget.ListView").index(2)))))));

        UiObject friends = clickFriends.getChild(new UiSelector()
             .className("android.widget.RelativeLayout").index(3));
        friends.click();
        sleep(timeout);

        //Update the status
        UiObject updateStatus = mDevice.findObject(new UiSelector().resourceId(
                                             "com.facebook.katana:id/publisher_status"));

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
        mDevice.pressHome();
    }

    //disable update using playstore
    public void disableUpdate() throws UiObjectNotFoundException {

        UiObject accountSelect = mDevice.findObject(new UiSelector()
                 .className("android.widget.Button").text("Accept"));

        if (accountSelect.exists())
             accountSelect.click();

        UiObject moreOptions = mDevice.findObject(new UiSelector()
                 .className("android.widget.ImageButton")
                 .description("More options"));
        moreOptions.click();

        UiObject settings = mDevice.findObject(new UiSelector()
                 .className("android.widget.TextView").text("Settings"));
        settings.clickAndWaitForNewWindow();

        UiObject autoUpdate = mDevice.findObject(new UiSelector()
                 .className("android.widget.TextView")
                 .text("Auto-update apps"));

        autoUpdate.clickAndWaitForNewWindow();

        UiObject clickAutoUpdate = mDevice.findObject(new UiSelector()
                  .className("android.widget.CheckedTextView")
                  .text("Do not auto-update apps"));

        clickAutoUpdate.clickAndWaitForNewWindow();

        mDevice.pressBack();
        mDevice.pressHome();
    }
}
