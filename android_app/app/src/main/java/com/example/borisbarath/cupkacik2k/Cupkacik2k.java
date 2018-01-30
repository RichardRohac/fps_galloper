package com.example.borisbarath.cupkacik2k;

import android.annotation.SuppressLint;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;

import com.github.nkzawa.socketio.client.IO;
import com.github.nkzawa.socketio.client.Socket;

import java.net.URISyntaxException;
import java.util.ArrayList;

public class Cupkacik2k extends AppCompatActivity implements SensorEventListener {

    private Socket socket;
    private SensorManager sensorManager;
    private Sensor sensor;
    private Sensor compass;
    private Button button;
    private Sensor accelerometer;
    private Sensor mag;
    String SERVER = "http://192.168.137.1:8080";
//    String SERVER = "http://192.168.137.74:8080";


    private ArrayList<Float> headings;
    private ArrayList<Float> pitches;
    private Float pitch = 0f;

    private final float[] mAccelerometerReading = new float[3];
    private final float[] mMagnetometerReading = new float[3];

    private final float[] mRotationMatrix = new float[9];
    private final float[] mOrientationAngles = new float[3];


    public Cupkacik2k() {
    }

    @SuppressLint("ClickableViewAccessibility")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cupkacik2k);

        headings = new ArrayList<>();
        pitches = new ArrayList<>();

        button = findViewById(R.id.shoot);
//        button.setOnTouchListener(new View.OnTouchListener() {
//            @Override
//            public boolean onTouch(View view, MotionEvent event) {
//                if(event.getAction() == MotionEvent.ACTION_DOWN) {
//                    //enableAim();
//                } else if (event.getAction() == MotionEvent.ACTION_UP) {
//                    //disableAim();
//                }
//
//                return false;
//            }
//        });


        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        sensor = sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR);
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        mag = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        //Stupne
        compass = sensorManager.getDefaultSensor(Sensor.TYPE_ORIENTATION);

        sensorManager.registerListener(new SensorEventListener() {
            @Override
            public void onSensorChanged(SensorEvent event) {

//                Log.i("SensorZ: ", Float.toString(event.values[2]));
//                Log.i("SensorY: ", Float.toString(event.values[1]));
//                Log.i("SensorX: ", Float.toString(event.values[0]));


//                up_down(acc[0]);
            }

            @Override
            public void onAccuracyChanged(Sensor sensor, int i) {}
        }, sensor, 4);

        sensorManager.registerListener(new SensorEventListener() {
            @Override
            public void onSensorChanged(SensorEvent sensorEvent) {

                heading(sensorEvent.values[0]);
            }

            @Override
            public void onAccuracyChanged(Sensor sensor, int i) {

            }
        }, compass, 3);

        sensorManager.registerListener(this, accelerometer,
                SensorManager.SENSOR_DELAY_FASTEST, SensorManager.SENSOR_DELAY_GAME);
        sensorManager.registerListener(this, mag,
                SensorManager.SENSOR_DELAY_FASTEST, SensorManager.SENSOR_DELAY_GAME);


        try {
            this.socket = IO.socket(SERVER);
        } catch (URISyntaxException e) {}

        try {
            this.socket.connect();
        } catch (Exception e) {
            Log.i("Exception", e.getMessage());
        }
    }
    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            System.arraycopy(event.values, 0, mAccelerometerReading,
                    0, mAccelerometerReading.length);
        }
        else if (event.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            System.arraycopy(event.values, 0, mMagnetometerReading,
                    0, mMagnetometerReading.length);
        }

        updateOrientationAngles();
    }

    // Compute the three orientation angles based on the most recent readings from
    // the device's accelerometer and magnetometer.
    public void updateOrientationAngles() {
        // Update rotation matrix, which is needed to update orientation angles.
        sensorManager.getRotationMatrix(mRotationMatrix, null,
                mAccelerometerReading, mMagnetometerReading);

        // "mRotationMatrix" now has up-to-date information.

        sensorManager.getOrientation(mRotationMatrix, mOrientationAngles);

        // "mOrientationAngles" now has up-to-date information.
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int i) {

    }

    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if ((keyCode == KeyEvent.KEYCODE_VOLUME_DOWN)){
            Log.i("ButtonPress", "WeaponReload");
            shoot();
        } else if ((keyCode == KeyEvent.KEYCODE_VOLUME_UP)){
            enableAim();
        }
        return true;
    }

    public boolean onKeyUp(int keyCode, KeyEvent event) {
        if ((keyCode == KeyEvent.KEYCODE_VOLUME_UP)){
            disableAim();
        }
        return true;
    }

    private void shoot() {
        this.socket.emit("shoot", "Shoot\n");
    }

    private void enableAim() {
        this.socket.emit("aimEnable");
    }

    private void disableAim() {
        this.socket.emit("aimDisable");
    }


    private void heading(float accZ) {
        int N = 2;
        headings.add(accZ);
        if (headings.size() == N) {
            //Log.i("OUT: ", Float.toString(headings.get(N -1)));
            String msg = Float.toString(-1 * headings.get(N -1)) + "," + mOrientationAngles[1];
            this.socket.emit("heading", msg);
            headings.clear();
        }
    }

    private void change_weapon() {
        this.socket.emit("change_weapon");
    }

    private void reload() {
        this.socket.emit("reload");
    }
}
