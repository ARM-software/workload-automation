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


package com.arm.wlauto.uiauto.videostreaming;

import android.app.Activity;
import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.BaseUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Date;
import java.util.concurrent.TimeUnit;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "videostreaming";

    /*function to convert time in string to sec*/
    public int computeTimeInSec(String time) {
        final int seconds = 60;
        if (!time.contains(":"))
           return -1;

        int totalTime = 0, mulfactor = 1;
        String [] strArr = time.split(":");

        for (int j = strArr.length - 1; j >= 0; j--) {
           totalTime += Integer.parseInt(strArr[j]) * (mulfactor);
           mulfactor = mulfactor * seconds;
        }
        return totalTime;
    }

@Test
public void runUiAutomation() throws Exception {
        final int timeout = 5;
        int currentTime = 0, timeAfter20Sec = 0, videoTime = 0;
        long timeBeforeGetText = 0, timeAfterGetText = 0, timeForGetText = 0;
        Bundle status = new Bundle();

        initialize_instrumentation();
        Bundle parameters = getParams();
        if (parameters.size() <= 0)
           return;

        int tolerance = parameters.getInt("tolerance");
        int samplingInterval = parameters.getInt("sampling_interval");
        String videoName = parameters.getString("video_name");

        UiObject search =mDevice.findObject(new UiSelector()
             .className("android.widget.ImageButton").index(0));
        if (search.exists()) {
           search.clickAndWaitForNewWindow(timeout);
        }

        UiObject clickVideoTab =mDevice.findObject(new UiSelector()
             .className("android.widget.Button").text("Video"));
        clickVideoTab.click();

        UiObject enterKeyword =mDevice.findObject(new UiSelector()
             .className("android.widget.EditText")
             .text("Please input the keywords"));
        enterKeyword.clearTextField();
        enterKeyword.setText(videoName);

        UiSelector selector = new UiSelector();
        UiObject clickSearch = mDevice.findObject(selector.resourceId("tw.com.freedi.youtube.player:id/startSearchBtn"));
        clickSearch.clickAndWaitForNewWindow(timeout);

        UiObject clickVideo =mDevice.findObject(new UiSelector().className("android.widget.TextView").textContains(videoName));
        if (!clickVideo.waitForExists(TimeUnit.SECONDS.toMillis(10))) {
            if (!clickVideo.exists()) {
                throw new UiObjectNotFoundException("Could not find video.");
            }
        }

        clickVideo.clickAndWaitForNewWindow(timeout);

        UiObject totalVideoTime =mDevice.findObject(new UiSelector()
             .className("android.widget.TextView").index(2));

        UiObject rewind =mDevice.findObject(new UiSelector()
             .className("android.widget.RelativeLayout")
             .index(0).childSelector(new UiSelector()
             .className("android.widget.LinearLayout")
             .index(1).childSelector(new UiSelector()
             .className("android.widget.LinearLayout")
             .index(1).childSelector(new UiSelector()
             .className("android.widget.ImageButton")
             .enabled(true).index(2)))));
        rewind.click();

        videoTime = computeTimeInSec(totalVideoTime.getText());

        /**
         * Measure the video elapsed time between sampling intervals and
         * compare it against the actual time elapsed minus tolerance.If the
         * video elapsed time is less than the (actual time elapsed -
         * tolerance), raise the message.
         */
        if (videoTime > samplingInterval) {
           for (int i = 0; i < (videoTime / samplingInterval); i++) {
              UiObject videoCurrentTime =mDevice.findObject(new UiSelector()
                 .className("android.widget.TextView").index(0));

              sleep(samplingInterval);

              // Handle the time taken by the getText function
              timeBeforeGetText = new Date().getTime() / 1000;
              timeAfter20Sec = computeTimeInSec(videoCurrentTime.getText());
              timeAfterGetText = new Date().getTime() / 1000;
              timeForGetText = timeAfterGetText - timeBeforeGetText;

              if (timeAfter20Sec == -1) {
                 mDevice.pressHome();
                 return;
              }

              if ((timeAfter20Sec - (currentTime + timeForGetText)) <
                         (samplingInterval - tolerance)) {
                 mDevice.pressHome();

                 mInstrumentation.sendStatus(Activity.RESULT_CANCELED,
                      status);
                 return;
              }
              currentTime = timeAfter20Sec;

         }
       } else {
            sleep(videoTime);
       }
       mDevice.pressBack();
       mDevice.pressHome();
       mInstrumentation.sendStatus(Activity.RESULT_OK, status);
    }
}
