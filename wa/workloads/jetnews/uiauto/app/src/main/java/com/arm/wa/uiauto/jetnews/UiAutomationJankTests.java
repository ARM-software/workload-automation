/*    Copyright 2024 ARM Limited
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

package com.arm.wa.uiauto.jetnews;

import androidx.test.jank.GfxMonitor;
import androidx.test.jank.JankTest;
import androidx.test.jank.JankTestBase;
import android.os.Bundle;

// UiAutomator 1 imports.
import androidx.test.uiautomator.UiScrollable;
import androidx.test.uiautomator.UiSelector;
import androidx.test.uiautomator.UiObject;

// UiAutomator 2 imports.
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.Direction;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;

import androidx.test.espresso.matcher.ViewMatchers;
import org.hamcrest.CoreMatchers;

import android.util.Log;

import java.util.Arrays;

import com.arm.wa.uiauto.ActionLogger;

// This class is responsible for actually running the UiAutomation
// tests and measuring the frame metrics. It will be invoked directly
// by workload-automation. We use an instance of UiAutomation so
// things get setup properly (parameters, screen orientation etc).

public class UiAutomationJankTests extends JankTestBase {
    private static final int DEFAULT_BENCHMARK_REPEAT_COUNT = 5;
    private static final int DEFAULT_TIMEOUT = 100;
    private static final int DEFAULT_BENCHMARK_FLING_SPEED = 20000;
    private static final String[] DEFAULT_BENCHMARK_TESTS
        = {"PortraitVerticalTest",
           "PortraitHorizontalTest",
           "LandscapeVerticalTest"};
    private static final String PACKAGE_NAME = "com.example.jetnews";
    private static final String LOG_TAG = "JetNewsJankTests: ";

    private static final String MAIN_VIEW = "ArticlesMainScrollView";
    private static final String TOP_ARTICLE = "TopStoriesForYou";
    private static final String FIRST_POST = "PostCardSimple0";
    private static final String FIRST_POST_CONTENT = "PostContent0";
    private static final String ARTICLE_VIEW = "ArticleView";
    private static final String BOTTOM_ARTICLE = "PostCardHistory19";
    private static final String POPULAR_LIST = "PopularOnJetnewsRow";
    private static final String ARTICLE_PREVIEW = "ArticleHomeScreenPreview0";
    private static final String FIRST_POPULAR_CARD = "PostCardPopular0";
    private static final String LAST_POPULAR_CARD = "PostCardPopular10";

    private UiAutomation mUiAutomation;
    private int repeat;
    private int fling_speed;
    private String[] tests;
    private UiDevice mDevice;
    private boolean testPortraitVertical;
    private boolean testPortraitHorizontal;
    private boolean testLandscapeVertical;

    @JankTest(
        expectedFrames = 100,
        defaultIterationCount = 1
    )

    @GfxMonitor(processName = PACKAGE_NAME)
    public void test1() throws Exception {
        for (int i = 0; i < repeat; i++) {
            if (testPortraitVertical) {
                ActionLogger logger
                    = new ActionLogger("PortraitVerticalTest",
                                       mUiAutomation.getParams());
                logger.start();
                resetAppState();
                runPortraitVerticalTests();
                logger.stop();
            }

            if (testPortraitHorizontal) {
                ActionLogger logger
                    = new ActionLogger("PortraitHorizontalTest",
                                       mUiAutomation.getParams());
                logger.start();
                resetAppState();
                runPortraitHorizontalTests();
                logger.stop();
            }

            if (testLandscapeVertical) {
                ActionLogger logger
                    = new ActionLogger("LandscapeVerticalTest",
                                       mUiAutomation.getParams());
                logger.start();
                resetAppState();
                runLandscapeVerticalTests();
                logger.stop();
            }
        }
    }

    // Returns true if the main view is in focus. False otherwise.
    private boolean findMainView() throws Exception {
        return mDevice.wait(Until.findObject(By.res(MAIN_VIEW)), DEFAULT_TIMEOUT) != null;
    }

    // Scroll the object with resource id ARTICLES_ID to the bottom end and
    // back to the top end. It is also used to scroll sideways if the controls
    // allow such movement.
    private void scrollList(String articles_id, String top_id, String bottom_id,
                            boolean sideways) throws Exception {
        // Scroll down and up in the articles list.
        assert(scrollTo(articles_id, bottom_id, true, top_id,
                        bottom_id, sideways, true, fling_speed));
        assert(scrollTo(articles_id, top_id, false, top_id,
                        bottom_id, sideways, true, fling_speed));
    }

    // Scroll the object with resource id ARTICLES_ID down until the object with
    // resource id ARTICLE_NAME is visible and return true. If the object is not
    // visible, return false.
    private boolean scrollToArticle(String articles_id,
                                      String article_name) throws Exception {
        // Scroll downwards until we find the item named ARTICLE_NAME on screen.
        // We reduce the fling speed so we don't skip past it on devices with
        // screens that are too small (less area to display things) or too
        // big (fast scrolling).
        scrollTo(articles_id, article_name, true, TOP_ARTICLE, BOTTOM_ARTICLE,
                 false, true, 1000);

        return mDevice.findObject(By.res(article_name)) != null;
    }

    // Assuming an object with resource id ARTICLE_ID is in view, click it,
    // wait for the article to open, fling downwards and upwards.
    //
    // This is shared with landscape mode as well, so we don't try to back out
    // from the opened article, since landscape mode presents a split view of
    // the scroll list and the article's contents.
    private void interactWithArticle(String article_id) throws Exception {
        UiObject2 article
            = mDevice.wait(Until.findObject(By.res(article_id)),
                           DEFAULT_TIMEOUT);

        ViewMatchers.assertThat(article, CoreMatchers.notNullValue());

        article.click();

        // Wait for the clicked article to appear.
        UiObject2 article_view
            = mDevice.wait(Until.findObject(By.res(ARTICLE_PREVIEW)),
                           DEFAULT_TIMEOUT);

        // If it is a small screen device or portrait mode, we may not have a
        // preview window, so look for a fullscreen article view.
        if (article_view == null) {

            article_view
                = mDevice.wait(Until.findObject(By.res(FIRST_POST_CONTENT)),
                               DEFAULT_TIMEOUT);
        }

        // Interact with the opened article by flinging up and down once.
        ViewMatchers.assertThat(article_view, CoreMatchers.notNullValue());
        article_view.setGestureMarginPercentage(0.2f);
        article_view.fling(Direction.DOWN, fling_speed);
        article_view.fling(Direction.UP, fling_speed);

        UiObject2 refresh_button
            = mDevice.wait(Until.findObject(By.text("Retry")),
                           DEFAULT_TIMEOUT);

        if (refresh_button != null)
            refresh_button.click();
    }

    // Reset the app state for a new test.
    private void resetAppState() throws Exception {
        mDevice.setOrientationPortrait();

        // FIXUP for differences between tablets and small phones.
        // Sometimes, when flipping back from landscape to portrait, the app
        // will switch to a view of the article, and we might need to back out
        // to the main view.
        UiObject2 article_view
            = mDevice.wait(Until.findObject(By.res(FIRST_POST_CONTENT)),
                           DEFAULT_TIMEOUT);

        // If we see the article view, back out from it.
        if (article_view != null)
            mDevice.pressBack();

        mDevice.setOrientationNatural();

        // Now make sure the main view is visible.
        while (mDevice.wait(Until.findObject(By.res(MAIN_VIEW)),
               DEFAULT_TIMEOUT) == null) {};

        // Scroll up to the top of the articles list.
        scrollTo(MAIN_VIEW, TOP_ARTICLE, false, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, fling_speed);
    }

    private void runPortraitVerticalTests() throws Exception {
        mDevice.setOrientationPortrait();

        assert(findMainView());
        scrollList(MAIN_VIEW, TOP_ARTICLE, BOTTOM_ARTICLE, false);
        assert(scrollToArticle(MAIN_VIEW, FIRST_POST));
        interactWithArticle(FIRST_POST);
    }

    private void runPortraitHorizontalTests() throws Exception {
        mDevice.setOrientationPortrait();

        assert(findMainView());
        scrollList(MAIN_VIEW, TOP_ARTICLE, BOTTOM_ARTICLE, false);
        assert(scrollToArticle(MAIN_VIEW, "PostCardHistory0"));
        assert(scrollToArticle(MAIN_VIEW, POPULAR_LIST));

        // Scroll the horizontal list to the end and back.
        scrollList(POPULAR_LIST, FIRST_POPULAR_CARD, LAST_POPULAR_CARD, true);
        // Fetch the first article on the horizontal scroll list.
        interactWithArticle(FIRST_POPULAR_CARD);
    }

    private void runLandscapeVerticalTests() throws Exception {
        // Flip the screen sideways to exercise the other layout
        // of the Jetnews app.
        mDevice.setOrientationLandscape();

        assert(findMainView());
        scrollList(MAIN_VIEW, TOP_ARTICLE, BOTTOM_ARTICLE, false);
        assert(scrollToArticle(MAIN_VIEW, FIRST_POST));
        interactWithArticle(FIRST_POST);
    }

    private boolean scrollTo(String element_id,
                             String resourceId, boolean downFirst,
                             String beginningId, String endId, boolean sideways,
                             boolean fling, int swipeSpeed) {
        // First check if the resource is in view. If it is, then just return.
        if (mDevice.wait(Until.findObject(By.res(resourceId)),
                         DEFAULT_TIMEOUT) != null) {
            Log.d(LOG_TAG, "Object " + resourceId + " was already in view.");
            return true;
        }

        Direction direction;
        String markerId = downFirst? endId:beginningId;

        if (sideways) {
            direction = downFirst? Direction.RIGHT:Direction.LEFT;
        }
        else {
            direction = downFirst? Direction.DOWN:Direction.UP;
        }

        for (int i = 0; i < 2; i++) {
            // Scroll to find the object.
            Log.d(LOG_TAG,
                  "Object " + resourceId + " is not in view. Scrolling.");
            do {
                UiObject2 element = mDevice.wait(Until.findObject(By.res(element_id)),
                                                 DEFAULT_TIMEOUT);
                element.setGestureMarginPercentage(0.2f);

                if (fling)
                    element.fling(direction, swipeSpeed);
                else
                    element.scroll(direction, 0.3f);

                UiObject2 refresh_button
                    = mDevice.wait(Until.findObject(By.text("Retry")),
                                   DEFAULT_TIMEOUT);

                if (refresh_button != null) {
                    refresh_button.click();
                }

                // If we found it, just return. Otherwise keep going.
                if (mDevice.wait(Until.findObject(By.res(resourceId)),
                                 DEFAULT_TIMEOUT) != null) {
                    Log.d(LOG_TAG,
                          "Object " + resourceId + " found while scrolling.");
                    return true;
                }

            } while (mDevice.wait(Until.findObject(By.res(markerId)),
                                  DEFAULT_TIMEOUT) == null);

            if (direction == Direction.DOWN)
                direction = Direction.UP;
            else if (direction == Direction.UP)
                direction = Direction.DOWN;
            else if (direction == Direction.RIGHT)
                direction = Direction.LEFT;
            else
                direction = Direction.RIGHT;

            Log.d(LOG_TAG, "Reached the limit at " + markerId + ".");

            if (markerId == beginningId)
                markerId = endId;
            else
                markerId = beginningId;
        }
        // We should've found it. If it is not here, it doesn't exist.
        return false;
    }

    @Override
    public void setUp() throws Exception {
        super.setUp();

        Log.d(LOG_TAG, "Initializing UiAutomation object.");
        mUiAutomation = new UiAutomation ();
        mUiAutomation.initialize_instrumentation();
        mUiAutomation.initialize();
        mUiAutomation.setup();

        // Check the parameters and set sane defaults.
        mDevice = mUiAutomation.mDevice;
        Bundle parameters = mUiAutomation.getParams();

        repeat = parameters.getInt("repeat");
        Log.d(LOG_TAG,"Argument \"repeat\": " + String.valueOf (repeat));
        if (repeat <= 0) {
            repeat = DEFAULT_BENCHMARK_REPEAT_COUNT;
            Log.d(LOG_TAG, "Argument \"repeat\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_REPEAT_COUNT));
        }

        fling_speed = parameters.getInt("flingspeed");
        Log.d(LOG_TAG,
              "Argument \"flingspeed\": " + String.valueOf (fling_speed));
        if (fling_speed <= 1000 || fling_speed >= 30000) {
            fling_speed = DEFAULT_BENCHMARK_FLING_SPEED;
            Log.d(LOG_TAG, "Argument \"flingspeed\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_FLING_SPEED));
        }

        String[] tests = parameters.getStringArray("tests");
        if (tests == null) {
            tests = DEFAULT_BENCHMARK_TESTS;
            Log.d(LOG_TAG, "Argument \"tests\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_TESTS));
        }

        Arrays.sort (tests);
        testPortraitVertical
            = Arrays.binarySearch(tests,
                                  "PortraitVerticalTest") >= 0? true : false;
        testPortraitHorizontal
            = Arrays.binarySearch(tests,
                                  "PortraitHorizontalTest") >= 0? true : false;
        testLandscapeVertical
            = Arrays.binarySearch(tests,
                                  "LandscapeVerticalTest") >= 0? true : false;

        if (testPortraitVertical)
            Log.d(LOG_TAG, "Found PortraitVerticalTest");
        if (testPortraitHorizontal)
            Log.d(LOG_TAG, "Found PortraitHorizontalTest");
        if (testLandscapeVertical)
            Log.d(LOG_TAG, "Found LandscapeVerticalTest");
    }
}
