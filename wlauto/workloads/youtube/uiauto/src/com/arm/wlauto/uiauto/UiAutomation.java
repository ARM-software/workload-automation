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
    public static final int WAIT_FOR_EXISTS_TIMEOUT = 1000;
    public static final int WAIT_OBJECT_TIMEOUT = 4; // in seconds
    public static final int SOURCE_MY_VIDEOS = 1;
    public static final int SOURCE_SEARCH = 2;
    public static final int SOURCE_TRENDING = 3;

    protected long networkTimeout =  TimeUnit.SECONDS.toMillis(20);
    protected String[] streamQuality = {
        "Auto", "144p", "240p", "360p", "480p", "720p", "1080p"
    };

    protected LinkedHashMap<String, Timer> results = new LinkedHashMap<String, Timer>();
    protected Bundle parameters;
    protected boolean dumpsysEnabled;
    protected String outputDir;
    protected String packageID;
    protected int videoSource;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        packageID = parameters.getString("package") + ":id/";
        videoSource = parseVideoSource(parameters.getString("video_source"));
        clearFirstRunDialogues();
        testPlayVideo(videoSource);
        seekForward();
        makeFullscreen();
        // changeQuality(streamQuality[1]);
        if (false) {
            writeResultsToFile(results, parameters.getString("output_file"));
        }
    }

    public int parseVideoSource(String source) throws Exception {
        if ("my_videos".equalsIgnoreCase(source)) {
            return SOURCE_MY_VIDEOS;
        } else if ("search".equalsIgnoreCase(source)) {
            return SOURCE_SEARCH;
        } else {
            return SOURCE_TRENDING;
        }
    }

    public void clearFirstRunDialogues() throws Exception {
        UiObject laterButton = new UiObject(new UiSelector().textContains("Later").className("android.widget.TextView"));
        if (laterButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
           laterButton.click();
        }
        UiObject cancelButton = new UiObject(new UiSelector().textContains("Cancel").className("android.widget.Button"));
        if (cancelButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            cancelButton.click();
        }
        UiObject skipButton = new UiObject(new UiSelector().textContains("Skip").className("android.widget.TextView"));
        if (skipButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            skipButton.click();
        }
        UiObject gotItButton = new UiObject(new UiSelector().textContains("Got it").className("android.widget.Button"));
        if (gotItButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            gotItButton.click();
        }
    }

    public void testPlayVideo(int source) throws Exception {
        if (source == SOURCE_MY_VIDEOS) {
            clickUiObject(BY_DESC, "Account");
        } else if (source == SOURCE_SEARCH) {
            clickUiObject(BY_DESC, "Search");
            UiObject textField = getUiObjectByResourceId(packageID + "search_edit_text");
            textField.setText("ARM Cortex");
            getUiDevice().pressEnter();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
        } else { // trending videos
            clickUiObject(BY_DESC, "Trending");
            clickUiObject(BY_ID, packageID + "thumbnail", true);
        }
    }

    public void makeFullscreen() throws Exception {
        UiObject fullscreenButton = getUiObjectByResourceId(packageID + "fullscreen_button",
                                                            "android.widget.ImageView");
        UiObject viewGroup =  getUiObjectByResourceId(packageID + "player_fragment", "android.widget.FrameLayout");
        viewGroup.click();
        waitObject(fullscreenButton, WAIT_OBJECT_TIMEOUT);
        fullscreenButton.click();
        sleep(4);
    }

    public void seekForward() throws Exception {
        UiObject timebar = getUiObjectByResourceId(packageID + "time_bar", "android.view.View");
        UiObject viewGroup =  getUiObjectByResourceId(packageID + "player_fragment", "android.widget.FrameLayout");
        viewGroup.click();
        waitObject(timebar, WAIT_OBJECT_TIMEOUT);
        timebar.click();
        sleep(4);
        // timebar.swipeRight(20);
        // sleep(2);
    }

    public void changeQuality(String quality) throws Exception {
        UiObject viewGroup =  getUiObjectByResourceId(packageID + "player_fragment", "android.widget.FrameLayout");
        viewGroup.click();
        UiObject moreOptions =  getUiObjectByResourceId(packageID + "player_overflow_button", "android.widget.ImageView");
        UiObject miniPlayerViewGroup =  getUiObjectByResourceId(packageID + "watch_player", "android.view.ViewGroup");
        UiObject miniPlayerViewLayout =  getUiObjectByResourceId(packageID + "watch_player", "android.widget.FrameLayout");

        // UiObject qualityButton =  getUiObjectByResourceId(packageID + "quality_button_text", "android.widget.TextView");

        // UiObject qualityButton =  new UiObject(new UiSelector().resourceId(packageID + "watch_player")
        //                                              .className("android.view.ViewGroup")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.FrameLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(0).className("android.widget.FrameLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(0).className("android.widget.RelativeLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.RelativeLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.ImageView")))))));

        UiObject qualityButton =  new UiObject(new UiSelector().descriptionContains("Show video quality menu"));
        UiObject qualitySetting =  getUiObjectByResourceId(quality, "android.widget.CheckedTextView");
        Log.v(TAG, String.format("MADE IT HERE"));
        waitObject(moreOptions, WAIT_OBJECT_TIMEOUT);
        moreOptions.click();

        if (miniPlayerViewGroup.exists()) {
            // MATE 8
            // miniPlayerViewGroup.click();
            UiObject frameLayout =  miniPlayerViewGroup.getChild(new UiSelector()
                                                            .index(1).className("android.widget.FrameLayout")
                                                            .childSelector(new UiSelector()));
        } else {
            // ZENFONE
            if (qualityButton.exists()) {
                qualityButton.click();
            }
            UiObject frameLayout =  miniPlayerViewLayout.getChild(new UiSelector()
                                                            .index(1).className("android.widget.FrameLayout")
                                                            .childSelector(new UiSelector()));
            int count = frameLayout.getChildCount();
            Log.v(TAG, String.format("ChildCount: %s", count));
            for (int i = 0; i < count ; i++) {
                String className = frameLayout.getChild(new UiSelector().index(i)).getClassName();
                String description = frameLayout.getChild(new UiSelector().index(i)).getContentDescription();
                Log.v(TAG, String.format("Child %s ClassName: %s %s", i, className, description));
            }
            throw new UiObjectNotFoundException(String.format("child count: %s", count));
        }
        // waitObject(qualityButton, WAIT_OBJECT_TIMEOUT);
        // qualityButton.click();
        // waitObject(qualitySetting, WAIT_OBJECT_TIMEOUT);
        // qualitySetting.click();
        // seekForward();
    }

}
