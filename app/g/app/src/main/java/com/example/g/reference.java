package com.example.g;

import androidx.appcompat.app.AppCompatActivity;

import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.concurrent.TimeUnit;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.text.format.DateUtils;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

public class reference extends AppCompatActivity {
    private TextToSpeech mTTs;
    private ImageButton mTTv;
    private TextView tv;
    private String text;
    private final int REQ_CODE = 100;
    private long value = 0;
    private String objectSearch="dog";
    private ArrayList<String> findertime;
    private ArrayList<String> finderobject;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.action);
        final FirebaseDatabase database = FirebaseDatabase.getInstance();
        DatabaseReference myRef = database.getReference("status");

        mTTv = findViewById(R.id.vbtn);
        tv = findViewById(R.id.tv);


        myRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {
                DatabaseReference stat = database.getReference("status");
                value = (long) dataSnapshot.getValue();
                if (value == 1) {
                    // This method is called once with the initial value and again
                    // whenever data at this location is updated.
                    getSpeech();
                }
                //Eugene this is for lost objects
                else if (value == 2) {
                    getSpeech();
                }

            }

            @Override
            public void onCancelled(DatabaseError error) {
                // Failed to read value

            }
        });

        mTTs = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int i) {
                if (i == TextToSpeech.SUCCESS) {
                    int result = mTTs.setLanguage(Locale.US);

                    if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                        Log.e("TTs", "Language not supported");
                    }
                }
            }
        });


    }

    private void speak(String text) {
        float pitch = .87f;
        float speed = .83f;

        mTTs.setPitch(pitch);
        mTTs.setSpeechRate(speed);
//        mTTs.setVoice(talk)

        ;

        mTTs.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
    }

    private void getSpeech() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "How can I help you?");
        // speak("What are you looking for?");

        if (intent.resolveActivity(getPackageManager()) != null)
            startActivityForResult(intent, REQ_CODE);
        else
            Toast.makeText(this, "Your Device is not supported", Toast.LENGTH_SHORT).show();
    }
    private String processlog (String message)
    {
        String[] strings = message.split(",");
        String output = "You have";
        for (int i=0;i<strings.length;i++)
        {
            output = output+strings[i].trim();
        }
        output = output + "next to your object";
        if (strings[1]=="")
            output="Nothing was found next to the object";
        return output;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        switch (requestCode) {
            case REQ_CODE: {
                if (resultCode == RESULT_OK && null != data) {
                    ArrayList<String> result = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                    text = (result.get(0) + "");
                    tv.setText(text);
                    if (value == 1) {
                        FirebaseDatabase database1 = FirebaseDatabase.getInstance();
                        DatabaseReference myRef1 = database1.getReference("status");
                        DatabaseReference myRef2 = database1.getReference("input");
                        myRef1.setValue(0);
                        myRef2.setValue(text);
                        speak(text);
                    } else if (value == 3) {
                        FirebaseDatabase.getInstance().getReference().child("log")
                                .addListenerForSingleValueEvent(new ValueEventListener() {
                                    @Override
                                    public void onDataChange(DataSnapshot dataSnapshot) {
                                        finderobject=new ArrayList<String>();
                                        findertime=new ArrayList<String>();
                                        for (DataSnapshot snapshot : dataSnapshot.getChildren()) {
                                            String time = snapshot.child("time").getValue(String.class);
                                            String objects = snapshot.child("object").getValue(String.class);
                                            finderobject.add(objects);
                                            findertime.add(time)
                                            ;
                                        }
                                        for (int i=finderobject.size()-1;i>=0;i--)
                                        {
                                            if(finderobject.get(i).contains(objectSearch))
                                            {
                                                String message =finderobject.get(i).replace(objectSearch,"");
                                                message=processlog(message);
                                                message = message + "last seen at" + findertime.get(i);
                                                tv.setText(message);
                                                //this would be working if speak worked
                                                break;
                                            }
                                        }
                                    }

                                    @Override
                                    public void onCancelled(DatabaseError databaseError) {
                                    }
                                });
                    }
                }
                break;
            }
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (mTTs != null) {
            mTTs.stop();
            mTTs.shutdown();
        }
    }
}