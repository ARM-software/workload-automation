package com.arm.wlauto.uiauto.gmail;

import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_gmail";

    private Bundle parameters;
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        Timer result = new Timer();
        result.start();

        clearFirstRunDialogues();

        clickNewMail();
        setToField();
        setSubjectField();
        setComposeField();
        clickSendButton();

        result.end();
        timingResults.put("Total", result);

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    public void clearFirstRunDialogues () throws Exception {
        // Enter search text into the file searchBox.  This will automatically filter the list.
        UiObject gotItBox = getUiObjectByResourceId("com.google.android.gm:id/welcome_tour_got_it",
                                                     "android.widget.TextView");
        gotItBox.clickAndWaitForNewWindow();
        UiObject takeMeToBox = getUiObjectByText("Take me to Gmail", "android.widget.TextView");
        takeMeToBox.clickAndWaitForNewWindow();
    }

    public void clickNewMail() throws Exception {
        Timer result = new Timer();
        UiObject newMailButton = getUiObjectByDescription("Compose", "android.widget.ImageButton");
        result.start();
        newMailButton.clickAndWaitForNewWindow(timeout);
        result.end();
        timingResults.put("newMail", result);
    }

    public void setToField() throws Exception {
        Timer result = new Timer();
        UiObject toField = getUiObjectByDescription("To", "android.widget.TextView");
        String recipient = parameters.getString("recipient").replace('_', ' ');
        result.start();
        toField.setText(recipient);
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("To", result);
    }

    public void setSubjectField() throws Exception {
        Timer result = new Timer();
        UiObject subjectField = getUiObjectByText("Subject", "android.widget.EditText");
        result.start();
        subjectField.setText("This is a test message");
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("Subject", result);
    }

    public void setComposeField() throws Exception {
        Timer result = new Timer();
        UiObject composeField = getUiObjectByText("Compose email", "android.widget.EditText");
        result.start();
        composeField.setText("This is a test composition");
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("Compose", result);
    }

    public void clickSendButton() throws Exception {
        Timer result = new Timer();
        UiObject sendButton = getUiObjectByDescription("Send", "android.widget.TextView");
        result.start();
        sendButton.clickAndWaitForNewWindow(timeout);
        result.end();
        timingResults.put("Send", result);
    }

    private void writeResultsToFile(LinkedHashMap timingResults, String file) throws Exception {
        // Write out the key/value pairs to the instrumentation log file
        FileWriter fstream = new FileWriter(file);
        BufferedWriter out = new BufferedWriter(fstream);
        Iterator<Entry<String, Timer>> it = timingResults.entrySet().iterator();

        while (it.hasNext()) {
            Map.Entry<String, Timer> pairs = it.next();
            Timer results = pairs.getValue();
            long start = results.getStart();
            long finish = results.getFinish();
            long duration = results.getDuration();
            out.write(String.format(pairs.getKey() + " " + start + " " + finish + " " + duration + "\n"));
        }
        out.close();
    }
}
