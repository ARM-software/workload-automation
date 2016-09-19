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

package com.arm.wlauto.uiauto.youtube;

import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String CLASS_BUTTON = "android.widget.Button";
    public static final String CLASS_TEXT_VIEW = "android.widget.TextView";

    public static final int WAIT_TIMEOUT_1SEC = 1000;
    public static final int VIDEO_SLEEP_SECONDS = 3;
    public static final int LIST_SWIPE_COUNT = 5;
    public static final String SOURCE_MY_VIDEOS = "my_videos";
    public static final String SOURCE_SEARCH = "search";
    public static final String SOURCE_TRENDING = "trending";

    protected ActionLogger logger;
    protected Bundle parameters;
    protected String packageName;
    protected String packageID;
    protected String videoSource;
    protected String searchTerm;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";
        videoSource = parameters.getString("video_source");
        searchTerm = parameters.getString("search_term");
        if (searchTerm != null) {
            searchTerm = searchTerm.replaceAll("0space0", " ");
        }

        setScreenOrientation(ScreenOrientation.NATURAL);
        clearFirstRunDialogues();
        disableAutoplay();
        testPlayVideo(videoSource, searchTerm);
        unsetScreenOrientation();
    }

    public void clearFirstRunDialogues() throws Exception {
        UiObject laterButton = new UiObject(new UiSelector().textContains("Later").className(CLASS_TEXT_VIEW));
        if (laterButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
           laterButton.click();
        }
        UiObject cancelButton = new UiObject(new UiSelector().textContains("Cancel").className(CLASS_BUTTON));
        if (cancelButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            cancelButton.click();
        }
        UiObject skipButton = new UiObject(new UiSelector().textContains("Skip").className(CLASS_TEXT_VIEW));
        if (skipButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            skipButton.click();
        }
        UiObject gotItButton = new UiObject(new UiSelector().textContains("Got it").className(CLASS_BUTTON));
        if (gotItButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            gotItButton.click();
        }
    }

    public void disableAutoplay() throws Exception {
        clickUiObject(BY_DESC, "More options");
        clickUiObject(BY_TEXT, "Settings", true);
        clickUiObject(BY_TEXT, "General", true);

        // Don't fail fatally if autoplay toggle cannot be found
        UiObject autoplayToggle = new UiObject(new UiSelector().textContains("Autoplay"));
        if (autoplayToggle.waitForExists(WAIT_TIMEOUT_1SEC)) {
            autoplayToggle.click();
        }
        getUiDevice().pressBack();

        // Tablet devices use a split with General in the left pane and Autoplay in the right so no
        // need to click back twice
        UiObject generalButton = new UiObject(new UiSelector().textContains("General").className(CLASS_TEXT_VIEW));
        if (generalButton.exists()) {
            getUiDevice().pressBack();
        }
    }

    public void testPlayVideo(String source, String searchTerm) throws Exception {
        if (SOURCE_SEARCH.equalsIgnoreCase(source)) {
            clickUiObject(BY_DESC, "Search");
            UiObject textField = getUiObjectByResourceId(packageID + "search_edit_text");
            textField.setText(searchTerm);
            getUiDevice().pressEnter();

            startMeasurements("play_search");
            // If a video exists whose title contains the exact search term, then play it
            // Otherwise click the first video in the search results
            UiObject thumbnail = new UiObject(new UiSelector().resourceId(packageID + "thumbnail"));
            UiObject matchedVideo = thumbnail.getFromParent(new UiSelector().textContains(searchTerm));
            if (matchedVideo.exists()) {
                matchedVideo.clickAndWaitForNewWindow();
            } else {
                thumbnail.clickAndWaitForNewWindow();
            }
            endMeasurements();
        } else if (SOURCE_MY_VIDEOS.equalsIgnoreCase(source)) {
            clickUiObject(BY_DESC, "Account");
            clickUiObject(BY_TEXT, "My Videos", true);

            startMeasurements("play_myvideos");
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements();
        } else if (SOURCE_TRENDING.equalsIgnoreCase(source)) {
            clickUiObject(BY_DESC, "Trending");

            startMeasurements("play_trending");
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements();
        } else { // homepage videos
            UiScrollable list = new UiScrollable(new UiSelector().resourceId(packageID + "results"));
            if (list.exists()) {
                list.scrollForward();
            }
            startMeasurements("play_home");
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements();
        }

        dismissAdvert();
        checkPlayerError();
        pausePlayVideo();
        checkVideoInfo();
        scrollRelated();
    }

    public void dismissAdvert() throws Exception {
        UiObject advert = new UiObject(new UiSelector().textContains("Visit advertiser"));
        if (advert.exists()) {
            UiObject skip = new UiObject(new UiSelector().textContains("Skip ad"));
            if (skip.waitForExists(WAIT_TIMEOUT_1SEC*5)) {
                skip.click();
                sleep(VIDEO_SLEEP_SECONDS);
            }
        }
    }

    public void checkPlayerError() throws Exception {
        UiObject playerError = new UiObject(new UiSelector().resourceId(packageID + "player_error_view"));
        UiObject tapToRetry = new UiObject(new UiSelector().textContains("Tap to retry"));
        if (playerError.waitForExists(WAIT_TIMEOUT_1SEC) || tapToRetry.waitForExists(WAIT_TIMEOUT_1SEC)) {
            throw new RuntimeException("Video player encountered an error and cannot continue.");
        }
    }

    public void pausePlayVideo() throws Exception {
        UiObject player = getUiObjectByResourceId(packageID + "player_fragment_container");
        sleep(VIDEO_SLEEP_SECONDS);
        repeatClickUiObject(player, 2, 100);
        sleep(1); // pause the video momentarily
        player.click();
        sleep(VIDEO_SLEEP_SECONDS);
    }

    public void checkVideoInfo() throws Exception {
        UiObject expandButton = new UiObject(new UiSelector().resourceId(packageID + "expand_button"));
        if (!expandButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            return;
        }
        // Expand video info
        expandButton.click();
        SystemClock.sleep(500); // short delay to simulate user action
        expandButton.click();
    }

    public void scrollRelated() throws Exception {
        // ListView of related videos and (maybe) comments
        UiScrollable list = new UiScrollable(new UiSelector().resourceId(packageID + "watch_list"));
        if (list.isScrollable()) {
            startMeasurements("scroll_down");
            list.flingToEnd(LIST_SWIPE_COUNT);
            endMeasurements();

            startMeasurements("scroll_up");
            list.flingToBeginning(LIST_SWIPE_COUNT);
            endMeasurements();
        }
        // After flinging, give the window enough time to settle down before
        // the next step, or else UiAutomator fails to find views in time
        sleep(VIDEO_SLEEP_SECONDS);
    }

    protected void startMeasurements(String testTag) throws Exception {
        logger = new ActionLogger(testTag, parameters);
        logger.start();
    }

    protected void endMeasurements() throws Exception {
        logger.stop();
    }
}
