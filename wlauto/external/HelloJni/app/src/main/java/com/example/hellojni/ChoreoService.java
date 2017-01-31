package com.example.hellojni;

import android.app.IntentService;
import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.Context;
import android.net.LocalServerSocket;
import android.net.LocalSocket;
import android.net.LocalSocketAddress;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Process;
import android.support.v7.app.NotificationCompat;
import android.util.Log;
import android.view.Choreographer;
import android.widget.Toast;

import java.io.IOException;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;

public class ChoreoService extends Service {
	static {
		System.loadLibrary("hello-jni");
	}

	private ServiceHandler mServiceHandler;

	/**
	 * A new instance of this class is created to handle each command.
	 * See https://developer.android.com/guide/components/services.html.
	 */
	private class SHFrameCallback implements Choreographer.FrameCallback {
		// ---- client management ----
		private int startId;

		// ---- vsync event handling ----
		private Choreographer chg;

		// ---- vsync logging ----
		/**
		 * Amount of logging data in bytes to buffer and write in one operation.
		 * Set this to 8 (i.e. sizeof(long)) to write out each timestamp as it occurs.
		 * Each entry takes up 8 bytes.
		 */
		private final static int LOG_BLOCK_SIZE = 8;
		/**
		 * Batches up logging data which is written once LOG_BLOCK_SIZE bytes have
		 * been accumulated. */
		ByteArrayOutputStream baos;
		/** The socket is created in the abstract namespace so the name is prepended with \0. */
		public final static String udsName = "vsync-uds";
		/** Accept socket waits for incoming connection. */
		private LocalServerSocket lss;
		/** Connection from client, as opposed to the accept socket. */
		private LocalSocket ls;
		/** Channel used to write vsync events to revent. */
		private OutputStream os;

		public SHFrameCallback(int startId) {
			Log.i("hjis:shfc:shfc", Integer.toString(startId));
			chg = Choreographer.getInstance();
			this.startId = startId;

			createUnixDomainSocket();

			requestNextFrame();
		}

		private void requestNextFrame() {
			chg.postFrameCallback(this);
		}

		/** This function is typically called when the remote end closes. */
		private void handleIOException(IOException ioe) {
			Log.i("hjis:shfc:hioe", ioe.getMessage());
            closeUnixDomainSocket(); // Remove to keep service running
			stopSelf();
		}

		// ---- vsync event handling ----

		/**
		 * Implements Choreographer.FrameCallback.
		 */
		public void doFrame(long frameTimeNanos) {
			logVsyncToUnixDomainSocket(frameTimeNanos);

			requestNextFrame();
		}

		// ---- vsync logging ----

		/**
		 * LocalServerSocket does not provide a way to handle an asynchronous
		 * connection, so this function does not return until the connection has
		 * been made.
		 */
		private void createUnixDomainSocket() {
			Log.i("hjis:shfc:ctuds", Integer.toString(startId));
			try {
				baos = new ByteArrayOutputStream(LOG_BLOCK_SIZE);

				lss = new LocalServerSocket(udsName);
				ls = lss.accept();
				os = ls.getOutputStream();
			} catch (IOException ioe) {
				Log.i("hjis:shfc:ctudsE", Integer.toString(startId));
				handleIOException(ioe);
			}
		}

		private void closeUnixDomainSocket() {
			Log.i("hjis:shfc:cluds", Integer.toString(startId));
			try {
				ls.shutdownOutput();
				ls.close();
				lss.close();
			} catch (IOException ioe) {
				Log.i("hjis:shfc:cludsE", Integer.toString(startId));
				handleIOException(ioe);
			}
		}

		private void logVsyncToUnixDomainSocket(long frameTimeNanos) {
			try {
				// Write frame time in little-endian format.
				for (int i = 0; i < 8; ++i) {
					baos.write((int) frameTimeNanos);
					frameTimeNanos >>= 8;
				}

				if (baos.size() == LOG_BLOCK_SIZE) {
					baos.writeTo(os);
					baos.reset();
				}
			} catch (IOException ioe) {
				Log.i("hjis:shfc:lvtudsE", Integer.toString(startId));
				handleIOException(ioe);
			}
		}
	}	// private class SHFrameCallback implements Choreographer.FrameCallback

	/**
	 * Exactly one instance of this service handler is created to handle all commands.
	 * An instance of SHFrameCallback stores the status of each command,
	 */
	public final class ServiceHandler extends Handler {
		public ServiceHandler(Looper lp) {
			super(lp);
		}

		@Override
		public void handleMessage(Message msg) {
			Log.i("hjis:sh:hm", Integer.toString(msg.arg1));

			new SHFrameCallback(msg.arg1);
		}
	}	// public final class ServiceHandler extends Handler {


	@Override
	public void onCreate() {
		Log.i("hjis:oc", "oc");
		// Create separate thread to run service.
		HandlerThread hthd = new HandlerThread("ServiceStartArguments");
        hthd.start();

		Looper lp = hthd.getLooper();
		mServiceHandler = new ServiceHandler(lp);


		Intent notificationIntent = new Intent(this, ChoreoService.class);

        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0,
                notificationIntent, 0);

        Notification notification = new NotificationCompat.Builder(this)
                .setContentIntent(pendingIntent).build();

        startForeground(1, notification);
    }

	/**
	 * This function is called every time that the service handles a command.
	 * Only one instance of ServiceHandler is used to handle all of the commands,
	 */
	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		Log.i("hjis:ocs", Integer.toString(startId));

		Message msg = mServiceHandler.obtainMessage();
		msg.arg1 = startId;
		mServiceHandler.sendMessage(msg);

		return START_STICKY;
//		return START_NOT_STICKY;
	}

	@Override
	public IBinder onBind(Intent intent) {
		// Binding not supported.
		return null;
	}

	@Override
	public void onDestroy() {
		Log.i("hjni:is:od", "od");
	}
}
