package com.arm.wlauto.uiauto.youtube;

import java.io.File;
import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Map;

import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String TAG = "youtube";
    public static final int WAIT_POPUP_TIMEOUT_MS = 1000;
    public static final int VIDEO_SLEEP_SECONDS = 5;
    public static final int LIST_SWIPE_COUNT = 1;
    public static final String SOURCE_MY_VIDEOS = "my_videos";
    public static final String SOURCE_SEARCH = "search";
    public static final String SOURCE_TRENDING = "trending";
    public static final String[] STREAM_QUALITY = {
        "Auto", "144p", "240p", "360p", "480p", "720p", "1080p"
    };

    protected LinkedHashMap<String, Timer> results = new LinkedHashMap<String, Timer>();
    protected Timer timer = new Timer();
    protected Bundle parameters;
    protected boolean dumpsysEnabled;
    protected String outputDir;
    protected String packageName;
    protected String packageID;
    protected String searchTerm;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        dumpsysEnabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
        packageName = parameters.getString("package");
        outputDir = parameters.getString("output_dir");
        packageID = packageName + ":id/";
        searchTerm = parameters.getString("search_term");
        if (searchTerm != null) {
            searchTerm = searchTerm.replaceAll("_", " ");
        }
        clearFirstRunDialogues();
        testPlayVideo(parameters.getString("video_source"), STREAM_QUALITY[0], searchTerm);
        writeResultsToFile(results, parameters.getString("output_file"));
    }

    public void clearFirstRunDialogues() throws Exception {
        UiObject laterButton = new UiObject(new UiSelector().textContains("Later").className("android.widget.TextView"));
        if (laterButton.waitForExists(WAIT_POPUP_TIMEOUT_MS)) {
           laterButton.click();
        }
        UiObject cancelButton = new UiObject(new UiSelector().textContains("Cancel").className("android.widget.Button"));
        if (cancelButton.waitForExists(WAIT_POPUP_TIMEOUT_MS)) {
            cancelButton.click();
        }
        UiObject skipButton = new UiObject(new UiSelector().textContains("Skip").className("android.widget.TextView"));
        if (skipButton.waitForExists(WAIT_POPUP_TIMEOUT_MS)) {
            skipButton.click();
        }
        UiObject gotItButton = new UiObject(new UiSelector().textContains("Got it").className("android.widget.Button"));
        if (gotItButton.waitForExists(WAIT_POPUP_TIMEOUT_MS)) {
            gotItButton.click();
        }
    }

    public void testPlayVideo(String source, String quality, String searchTerm) throws Exception {
        if (SOURCE_MY_VIDEOS.equalsIgnoreCase(source)) {
            startMeasurements();
            clickUiObject(BY_DESC, "Account");
            endMeasurements("tab_account");
            startMeasurements();
            clickUiObject(BY_TEXT, "My Videos", true);
            endMeasurements("tab_my_videos");
            startMeasurements();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements("player_my_videos");
        } else if (SOURCE_SEARCH.equalsIgnoreCase(source)) {
            startMeasurements();
            clickUiObject(BY_DESC, "Search");
            endMeasurements("tab_search");
            startTimer();
            UiObject textField = getUiObjectByResourceId(packageID + "search_edit_text");
            textField.setText(searchTerm);
            endTimer("search_video");
            getUiDevice().pressEnter();
            startMeasurements();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements("player_search");
        } else if (SOURCE_TRENDING.equalsIgnoreCase(source)) {
            startMeasurements();
            clickUiObject(BY_DESC, "Trending");
            endMeasurements("tab_trending");
            startMeasurements();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements("player_trending");
        } else { // homepage videos
            startMeasurements();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
            endMeasurements("player_home");
        }
        checkVideoInfo();
        seekForward();
        changeQuality(quality);
        makeFullscreen();
    }

    public void checkVideoInfo() throws Exception {
        // Expand video info
        startTimer();
        clickUiObject(BY_ID, packageID + "expand_button");
        endTimer("expand_info_card");
        SystemClock.sleep(500); // short delay to simulate user action
        clickUiObject(BY_ID, packageID + "expand_button");
        // Display share menu
        startTimer();
        clickUiObject(BY_ID, packageID + "share_button", true);
        endTimer("show_share_menu");
        SystemClock.sleep(500); // short delay to simulate user action
        getUiDevice().pressBack();
        // Scroll down the list of related videos and comments
        UiScrollable list = new UiScrollable(new UiSelector().resourceId(packageID + "watch_list"));
        if (list.isScrollable()) {
            startMeasurements();
            list.flingToEnd(LIST_SWIPE_COUNT);
            endMeasurements("watch_list_fling_down");
            startMeasurements();
            list.flingToBeginning(LIST_SWIPE_COUNT);
            endMeasurements("watch_list_fling_up");
        }
        // Give the window enough time to settle down before the next
        // step, or else complains about views not being found in time
        sleep(3);
    }

    public void seekForward() throws Exception {
        startMeasurements();
        clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        UiObject timebar = clickUiObject(BY_ID, packageID + "time_bar");
        endMeasurements("seekbar_touch");
        sleep(VIDEO_SLEEP_SECONDS);
    }

    public void makeFullscreen() throws Exception {
        startMeasurements();
        clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        clickUiObject(BY_ID, packageID + "fullscreen_button", true);
        endMeasurements("fullscreen_toggle");
        startDumpsys();
        sleep(VIDEO_SLEEP_SECONDS);
        endDumpsys("fullscreen_player");
    }

    public void changeQuality(String quality) throws Exception {
        UiObject player = clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        clickUiObject(BY_DESC, "More options");
        getUiDevice().waitForIdle();
        clickUiObject(BY_ID, packageID + "quality_button", true);
        clickUiObject(BY_TEXT, quality);
        sleep(VIDEO_SLEEP_SECONDS);
    }

    protected void startDumpsys() throws Exception {
        if (dumpsysEnabled) {
            initDumpsysSurfaceFlinger(packageName);
            initDumpsysGfxInfo(packageName);
        }
    }

    protected void endDumpsys(String testTag) throws Exception {
        if (dumpsysEnabled) {
            String dumpsysTag = TAG + "_" + testTag;
            exitDumpsysSurfaceFlinger(packageName, new File(outputDir, dumpsysTag + "_surfFlinger.log"));
            exitDumpsysGfxInfo(packageName, new File(outputDir, dumpsysTag + "_gfxInfo.log"));
        }
    }

    protected void startTimer() {
        timer = new Timer();
        timer.start();
    }

    protected void endTimer(String testTag) {
        timer.end();
        results.put(testTag, timer);
    }

    protected void startMeasurements() throws Exception {
        startDumpsys();
        startTimer();
    }

    protected void endMeasurements(String testTag) throws Exception {
        endTimer(testTag);
        endDumpsys(testTag);
    }
}
