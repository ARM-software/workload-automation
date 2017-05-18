package com.arm.wlauto.uiauto.appshare;

import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends UxPerfUiAutomation {

    // Create UIAutomation objects
    private com.arm.wlauto.uiauto.googlephotos.UiAutomation googlephotos =
        new com.arm.wlauto.uiauto.googlephotos.UiAutomation();

    private com.arm.wlauto.uiauto.gmail.UiAutomation gmail =
        new com.arm.wlauto.uiauto.gmail.UiAutomation();

    private com.arm.wlauto.uiauto.skype.UiAutomation skype =
        new com.arm.wlauto.uiauto.skype.UiAutomation();

    public Bundle parameters;

@Test
public void runUiAutomation() throws Exception {
        // Override superclass value
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(10);
        initialize_instrumentation();
        parameters = getParams();

        // Setup the three uiautomator classes with the correct information
        // Also create a dummy parameter to disable marker api as they
        // should not log actions themselves.
        Bundle dummyParams = new Bundle();
        dummyParams.putString("markers_enabled", "false");

        googlephotos.initialize_instrumentation();
        skype.initialize_instrumentation();
        gmail.initialize_instrumentation();

    String packageName = parameters.getString("googlephotos_package");
        googlephotos.setWorkloadParameters(dummyParams, packageName, packageName + ":id/");
        packageName = parameters.getString("gmail_package");
        gmail.setWorkloadParameters(dummyParams, packageName, packageName + ":id/");
        packageName = parameters.getString("skype_package");
        skype.setWorkloadParameters(dummyParams, packageName, packageName + ":id/");

        String recipient = parameters.getString("recipient");
        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");
        String contactName = parameters.getString("name");

        setScreenOrientation(ScreenOrientation.NATURAL);

        setupGooglePhotos();
        sendToGmail(recipient);
        logIntoSkype(loginName, loginPass);
        // Skype won't allow us to login and share on first visit so invoke
        // once more from googlephotos
        pressBack();

        // On some devices the first back press only hides the keyboard, check if
        // another is needed.
        UiObject googlephotosShare = mDevice.findObject(new UiSelector().packageName(
                                      parameters.getString("googlephotos_package")));
        if (!googlephotosShare.exists()){
            pressBack();
        }
        sendToSkype(contactName);

        unsetScreenOrientation();
    }

    private void setupGooglePhotos() throws Exception {
        googlephotos.dismissWelcomeView();
        googlephotos.closePromotionPopUp();
        selectGalleryFolder("wa-working");
        googlephotos.selectFirstImage();
    }

    private void sendToGmail(String recipient) throws Exception {
        String gID = gmail.getPackageID();

        shareUsingApp("Gmail", "gmail");

        gmail.clearFirstRunDialogues();

        UiObject composeView =
            mDevice.findObject(new UiSelector().resourceId(gID + "compose"));
        if (!composeView.waitForExists(uiAutoTimeout)) {
            // After the initial share request on some devices Gmail returns back
            // to the launching app, so we need to share the photo once more and
            // wait for Gmail to sync.
            shareUsingApp("Gmail", "gmail_retry");

            gmail.clearFirstRunDialogues();
        }

        gmail.setToField(recipient);
        gmail.setSubjectField();
        gmail.setComposeField();
        gmail.clickSendButton();
    }

    private void logIntoSkype(String loginName, String loginPass)  throws Exception {
        shareUsingApp("Skype", "skype_setup");

        skype.handleLoginScreen(loginName, loginPass);

        sleep(10); // Pause while the app settles before returning
    }

    private void sendToSkype(String contactName) throws Exception {
        shareUsingApp("Skype", "skype");

        skype.searchForContact(contactName);
        skype.dismissUpdatePopupIfPresent();

        sleep(10); // Pause while the app settles before returning
    }

    private void shareUsingApp(String appName, String tagName) throws Exception {
        String testTag = "share";
        ActionLogger logger = new ActionLogger(testTag + "_" + tagName, parameters);

        clickUiObject(BY_DESC, "Share", "android.widget.ImageView");
        UiScrollable applicationGrid =
            new UiScrollable(new UiSelector().resourceId(googlephotos.getPackageID() + "application_grid"));
        if (!applicationGrid.exists()){
            applicationGrid =
                new UiScrollable(new UiSelector().resourceId(googlephotos.getPackageID() + "share_expander"));
        }
        UiObject openApp =
            mDevice.findObject(new UiSelector().text(appName)
                                               .className("android.widget.TextView"));
        // On some devices the application_grid has many entries, so we have to swipe up to make
        // sure all the entries are visable.  This will also stop entries at the bottom being
        // obscured by the bottom action bar.
        applicationGrid.swipeUp(10);
        while (!openApp.exists()) {
            // In the rare case the grid is larger than the screen swipe up
            applicationGrid.swipeUp(10);
        }
        logger.start();
        openApp.clickAndWaitForNewWindow();
        logger.stop();
    }
}
