/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.example.hellojni;

import java.util.List;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.os.Handler;
import android.util.Log;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;

public class HelloJni extends AppCompatActivity {
    /* this is used to load the 'hello-jni' library on application
     * startup. The library has already been unpacked into
     * /data/data/com.example.hellojni/lib/libhello-jni.so at
     * installation time by the package manager.
     */
    static {
        System.loadLibrary("hello-jni");
    }

    private Handler h;
    private TextView tv;
    private int doneRandCalls;
    private static final int totalRandCalls = 10;

	public native static void nativeSrand(long seed);
	public native static int nativeRand();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_hello_jni);

		tv = (TextView) findViewById(R.id.text);
        h = new Handler();

       callSrand();
    }

	private void callSrand() {
		tv.setText("");

		nativeSrand(0x1234);
		appendMessage("Called srand");

		doneRandCalls = 0;
		h.postDelayed(
			new Runnable() {
				public void run() {
					callRand();
				}
			},
			/* delayMillis */ 1000);
	}

	private void callRand() {
		int randVal = nativeRand();
		String msg = String.format(
			"rand: %d/%d: %d", doneRandCalls, totalRandCalls, randVal);
		appendMessage(msg);

		++doneRandCalls;
		if (doneRandCalls == totalRandCalls)
			return;

		h.postDelayed(
			new Runnable() {
				public void run() {
					callRand();
				}
			},
			/* delayMillis */ 1000);
	}

	private void appendMessage(String st) {
		tv.append(st);
		tv.append("\n");
	}

	public void onRestartClick(View v) {
		h.removeCallbacksAndMessages(null);
		tv.setText("");
		callSrand();
	}

	public void onCloseClick(View v) {
		// finish() does not kill the process, so force the VM to shut down.
		System.exit(0);
	}

	/**
	 * This function is not needed to print random numbers or to
	 * run the vsync service.  However, the definition is left here
	 * it is a convenient way to list the available (not just loaded)
	 * packages.
	 */
	private void printAvailablePackages() {
		StringBuilder sb = new StringBuilder();
		List<PackageInfo> pkgs = getPackageManager().getInstalledPackages(PackageManager.GET_SERVICES);
		for (PackageInfo pkg : pkgs) {
			int scount = (pkg.services == null) ? 0 : pkg.services.length;
			String pkgst = String.format("%s (%d)%n", pkg.packageName, scount);
			sb.append(pkgst);

			if (pkg.services != null) {
				for (ServiceInfo si : pkg.services) {
					String svstr = String.format(" s: %s%n", si.name);
					sb.append(svstr);
				}
			}

			Log.i("hjni", sb.toString());
			sb.setLength(0);
		}
	}	// private void printAvailablePackages() {
}	// public class HelloJni extends AppCompatActivity {

