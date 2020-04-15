package com.example.g;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import java.util.Date;
import java.util.HashSet;
import java.util.concurrent.TimeUnit;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.text.format.DateUtils;
import android.util.Log;
import android.view.View;
import android.view.animation.TranslateAnimation;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.bumptech.glide.Glide;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.OnSuccessListener;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import com.google.firebase.storage.FirebaseStorage;
import com.google.firebase.storage.StorageReference;

import org.atteo.evo.inflector.English;

import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.text.SimpleDateFormat;
import java.util.Date;
import android.animation.*;
import android.graphics.Color;
import android.os.Vibrator;
import android.content.Context;


public class Action extends AppCompatActivity {
    private TextToSpeech mTTs;
    private SimpleDateFormat sdf = new SimpleDateFormat("yyyy.MM.dd G 'at' HH:mm:ss z");
    private String datetime = sdf.format(new Date());
    private ImageButton mTTv;
    private ImageButton vbtn2;
    private TextView tv;
    private String text;
    private String question;
    private StoreString store = new StoreString();
    private long value = 0;
    private final int REQ_CODE = 100;
    private long conf = 0;
    private long start = 0;
    private String answer = "";
    private boolean doneSpeaking;
    private String scan = "";
    private ArrayList<String> obarray = new ArrayList<String>();
    private String objectSearch;
    private ArrayList<String> findertime;
    private ArrayList<String> finderobject;
    private ArrayList<String> finderarray;
    private boolean found = false;
    private String read = "";
    private long pcol = 0;
    private long lol = 0;
    private boolean useLocations = true;
    private ArrayList<String> allclasses = new ArrayList<String>();
    final FirebaseDatabase database = FirebaseDatabase.getInstance();
    StorageReference sentRef;

    View myView;
    boolean isUp;

    private void fadeIn() {
        ObjectAnimator bounceX = ObjectAnimator.ofFloat(findViewById(R.id.vbtn2), "scaleX", 1.05f, 1f);
        ObjectAnimator bounceY = ObjectAnimator.ofFloat(findViewById(R.id.vbtn2), "scaleY", 1.05f, 1f);
        AnimatorSet animSetXY = new AnimatorSet();
        animSetXY.setDuration(1000);
        animSetXY.playTogether(bounceX, bounceY);
        animSetXY.addListener(new AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(Animator animation) {
                fadeOut();
            }
        });
        animSetXY.start();
    }

    private void fadeOut() {
        ObjectAnimator bounceX = ObjectAnimator.ofFloat(findViewById(R.id.vbtn2), "scaleX", 1f, 1.05f);
        ObjectAnimator bounceY = ObjectAnimator.ofFloat(findViewById(R.id.vbtn2), "scaleY", 1f, 1.05f);
        AnimatorSet animSetXY = new AnimatorSet();
        animSetXY.setDuration(1000);
        animSetXY.playTogether(bounceX, bounceY);
        animSetXY.addListener(new AnimatorListenerAdapter() {
            @Override
            public void onAnimationEnd(Animator animation) {
                fadeIn();
            }
        });
        animSetXY.start();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        fadeIn();

        getWindow().setStatusBarColor(Color.parseColor("#ff2c8d"));

        super.onCreate(savedInstanceState);
        setContentView(R.layout.action);
        DatabaseReference stat = database.getReference("status");
        DatabaseReference whole = database.getReference();
        DatabaseReference donesearch = database.getReference("searchdone");
        FirebaseStorage storage = FirebaseStorage.getInstance();
        final StorageReference storageRef = storage.getReference();
        sentRef = storageRef.child("sent.jpg");

        mTTv = findViewById(R.id.vbtn);
        vbtn2 = findViewById(R.id.vbtn2);
        pcol = 0;
        myView = findViewById(R.id.my_view);
        myView.setVisibility(View.INVISIBLE);
        isUp = false;

        tv = findViewById(R.id.tv);
        final ImageView image = findViewById(R.id.imageView);

        donesearch.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                long done = (long) dataSnapshot.getValue();
                DatabaseReference col = database.getReference("collide");
                Log.e("completed search", "done");

                if(done == 1)
                {
                    speak("Search completed");
                    pcol = 0;
                    DatabaseReference d = database.getReference("searchdone");
                    col.setValue(2);
                    d.setValue(0);
                    done = 0;
                }

            }
            @Override
            public void onCancelled(@NonNull DatabaseError databaseError) {

            }
        });

        whole.addValueEventListener(new ValueEventListener() { //monitors all, but just reads scan and text, and also changes value for datetime but DOES NOT change in firebase
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                scan = "" + dataSnapshot.child("scan/object").getValue();
                read = "" + dataSnapshot.child("text").getValue();
                answer = "" + dataSnapshot.child("answer").getValue();
                String array = dataSnapshot.child("scan/array").getValue(String.class);
                array = array.replace("[", "").replace("]", "").replace("'", "").replace(" ", "");
                DatabaseReference col = database.getReference("collide");
                long collide = (long) dataSnapshot.child("collide").getValue();
                sentRef = storageRef.child("sent.jpg");
                long done = (long) dataSnapshot.child("searchdone").getValue();

                if(!answer.equals("")) //ready
                {
                    speak(answer);
                    DatabaseReference an = database.getReference("answer");
                    an.setValue("");
                    resetFire(); //resets conf and  mode in firebase
                    Log.e("answer", answer);
                }

                if(scan.length() > 2)
                    if(scan.charAt(scan.length()-1) == ',')
                        scan = scan.substring(scan.length()-2);

                for(int i = 0; i < 10; i++)
                {
                    array = array.replace("" + i, "");
                }
                String[] s_ar = array.split(",");
                obarray = new ArrayList<String>();
                for(String s:s_ar)
                {
                    obarray.add(s);
                }

                sdf = new SimpleDateFormat("yyyy.MM.dd G 'at' HH:mm:ss z");
                datetime = sdf.format(new Date());

                if(collide == 1 && done == 0){
                    //speak("Collision Alert");
                    DatabaseReference d = database.getReference("searchdone");
                    d.setValue(0);
                }
                if(pcol!=collide && pcol == 1 && collide == 0)
                {
                    //speak("Safe");

                }
                pcol = collide;

            }

            @Override
            public void onCancelled(@NonNull DatabaseError databaseError) {
                Log.e("DATABASE ERROR", "Exited1");

            }
        });

        stat.addValueEventListener(new ValueEventListener() { //monitors status (confirm and mode) and is where each "mode" is processed
            @Override
            public int hashCode() {
                return super.hashCode();
            }

            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {

                DatabaseReference time = database.getReference("date-time");
                String x = time.toString();
                time.setValue("" + datetime);
                value = (long) dataSnapshot.child("mode").getValue();
                conf = (long) dataSnapshot.child("confirm").getValue();
                start = (long) dataSnapshot.child("start").getValue();

                Log.e("Mode", "" + value);
                Log.e("Start", "" + start);
                if(start == 1  && conf == 0) // firebase is mess but it works
                {
                    final long ONE_MEGABYTE = 6000000;

                    sentRef.getBytes(ONE_MEGABYTE).addOnSuccessListener(new OnSuccessListener<byte[]>() {
                        @Override
                        public void onSuccess(byte[] bytes) { //changing  pic
                            // Data for "sent.jpg" is returns, use this as needed
                            //imageView.setImageResource(R.drawable.my_image);
                            Bitmap bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);

                            image.setImageBitmap(Bitmap.createScaledBitmap(bmp, image.getWidth(),
                                    image.getHeight(), false));
                        }
                    }).addOnFailureListener(new OnFailureListener() {
                        @Override
                        public void onFailure(@NonNull Exception exception) {
                            Log.e("Failure", exception.getLocalizedMessage());
                        }
                    });


                }

                else if(conf == 1  && start == 1) //ready
                {
                    speak("How can I help you?");
                    getSpeech();
                    //resetFire(); //resets conf and  mode in firebase
                }
            }

            @Override
            public void onCancelled(DatabaseError error) {
                // Failed to read value
                Log.e("DATABASE ERROR", "Exited");

            }
        });


        vbtn2.setOnClickListener(new View.OnClickListener() { //don't need to manually change database
            @Override
            public void onClick(View v) {
                DatabaseReference start = database.getReference("status/start");
                DatabaseReference confirm = database.getReference("status/confirm");
                start.setValue(0);
                confirm.setValue(0);
                start.setValue(1);
                confirm.setValue(1);
                Vibrator vib = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
                vib.vibrate(200);
                slideDownAll(myView);
//                if(useLocations == false) {
//                    useLocations = true;
//                }
//                else {
//                    useLocations = false;
//                }
            }
        });

        mTTv.setOnClickListener(new View.OnClickListener() { //don't need to manually change database ///////////////////////////////////////////////////////////
            @Override
            public void onClick(View v) {
                onSlideViewButtonClick(myView);
                DatabaseReference collide = database.getReference("cheat");
                collide.addValueEventListener(new ValueEventListener() {
                    @Override
                    public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                        long col = (long) dataSnapshot.getValue();
                        DatabaseReference c = database.getReference("collide");

                        if(lol % 2 == 0)
                        {
                            c.setValue(1);
                        }
                        else
                        {
                            c.setValue(0);

                        }
                        lol++;

                    }

                    @Override
                    public void onCancelled(@NonNull DatabaseError databaseError) {

                    }
                });

            }
        });

        mTTs = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int i) {
                if(i == TextToSpeech.SUCCESS) {
                    int result = mTTs.setLanguage(Locale.US);

                    if(result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED ) {
                        Log.e("TTs", "Language not supported");
                    }}
            }
        });

    }

    public void slideUp(View view){
        view.setVisibility(View.VISIBLE);
        TranslateAnimation animate = new TranslateAnimation(
                0,                 // fromXDelta
                0,                 // toXDelta
                view.getHeight(),  // fromYDelta
                0);                // toYDelta
        animate.setDuration(300);
        animate.setFillAfter(true);
        view.startAnimation(animate);
        findViewById(R.id.imageView).setClickable(true);
    }

    public void slideDown(View view){
        TranslateAnimation animate = new TranslateAnimation(
                0,                 // fromXDelta
                0,                 // toXDelta
                0,                 // fromYDelta
                view.getHeight()); // toYDelta
        animate.setDuration(300);
        animate.setFillAfter(true);
        view.startAnimation(animate);
        findViewById(R.id.imageView).setClickable(false);
    }

    public void slideDownAll(View view) {
        if (isUp) {
            slideDown(myView);
            isUp = !isUp;
        }
    }

    public void onSlideViewButtonClick(View view) {
        if (isUp) {
            slideDown(myView);
        } else {
            slideUp(myView);
        }
        isUp = !isUp;
    }

    private void speak(String text){
        float pitch = .87f;
        float speed = .7f;

        mTTs.setPitch(pitch);
        mTTs.setSpeechRate(speed);
//        mTTs.setVoice(talk);

        mTTs.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
        int x = 0;
        while(mTTs.isSpeaking())
        {
            x++;
        }
    }

    private void resetFire(){
        DatabaseReference confirm = database.getReference("status/confirm");
        DatabaseReference mode = database.getReference("status/mode");
        DatabaseReference start = database.getReference("status/start");
        DatabaseReference in = database.getReference("input");
        DatabaseReference an = database.getReference("answer");
        DatabaseReference q = database.getReference("question");
        start.setValue(0);
        confirm.setValue(0);
        mode.setValue(0);
        in.setValue("");
        q.setValue("");
        an.setValue("");
    }

    private void getSpeech(){
        //speak("There are " + scan);
        speak(question);
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "How can I help you?");


        if(intent.resolveActivity(getPackageManager()) != null)
                startActivityForResult(intent, REQ_CODE);
        else
            Toast.makeText(this, "Your Device is not supported", Toast.LENGTH_SHORT).show();
    }

    private String processlog (String message)  //forms sentence
    {
        Log.e("process log", message);

        String[] strings = message.split(",");
        String[][] obs = new String[strings.length/2-1][2];
        int a = 0;
        for(int j  = 0; j < strings.length; j = j+2)
        {
            if(!objectSearch.equals(strings[j]))
            {
                obs[a][0] = strings[j];
                obs[a][1] = strings[j+1];
                a = a+1;
            }

        }

        String output = objectSearch + " last seen next to ";

        if (obs.length == 2)
            return objectSearch + " was last seen ";
        int num = 0;
        for (int i=0;i<obs.length;i++)
        {
                int pnum = Integer.parseInt(obs[i][1]);
                String word = Plural(obs[i][0], pnum);
                //String word = obs[i][0];
                if(i == obs.length -  2)
                    word = obs[i][1] + " " + word + ", and ";
                else if(i == obs.length-1)
                    word = obs[i][1] + " " + word;
                else
                    word = obs[i][1] + " " + word + ", ";


                output = output + word + " ";

        }

        return output;
    }

    private String Plural(String w, int num)
    {
        if(w.equals("person"))
        {
            return "people";
        }
        else{
            return English.plural(w);
        }
    }

    private String getWord (String voice,  ArrayList<String> ar)
    {
        ArrayList<String> ar2  = ar;

        Log.e("all classes", ar.toString());


        String[] m = voice.split(" ");
        int x = -1;
        for(String s:m){
            x++;
            Log.e("Word" + x, s);
            String word = English.plural(s, 1).toLowerCase();
            Log.e("word" + x, word);

            if(ar.contains(word) && word.length() > 2)
                return ar.get(ar.indexOf(word));
        }
        return voice;

//        String[] badwords = {"a ", "the ", "my "};
//        for(int i =0; i < badwords.length; i++)
//            s = s.replace(badwords[i], "");
//        Log.e("bad", s);
//        return s.replace("a ", "");
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        switch (requestCode) {
            case REQ_CODE: {
                if(null == data)
                {
                    tv.setText("");
                    resetFire();


                }
                else if (resultCode == RESULT_OK && null != data && start == 1) {
                    start = 0;

                    DatabaseReference startmode = database.getReference("status/start");
                    DatabaseReference confirm = database.getReference("status/confirm");

                    ArrayList<String> result = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                    ArrayList<String> modes = new ArrayList<String>();
                    modes.add("scan");
                    modes.add("text");
                    modes.add("find");
                    modes.add("search");
                    modes.add("help");
                    modes.add("nothing");
                    modes.add("repeat");
                    modes.add("nevermind");
                    modes.add("skin");
                    //use obarray


                    String ogtext = (result.get(0) + "");
                    store.setString(ogtext);
                    Log.e("Original text", ogtext);
                    String m = getWord(ogtext, modes);
                    Log.e("m: ", m);
                    String text = getWord(ogtext, obarray);
                    DatabaseReference input = database.getReference("input");

/*

 */
                    if(m.equals("search")){ ////////////////////////////////////done
                        if(obarray.contains(text))
                        {
                            input.setValue(text);
                            speak("Searching for " + text);

                        }
                        else
                        {
                            //speak("item not found");
                            resetFire();
                            input.setValue("null");
                        }
                        tv.setText(ogtext);
                        resetFire();

                    }
                    else if(m.equals("text")){ ////////////////////////////////////done
                        if(read.equals(""))
                            speak("No text found");
                        else
                            speak(read);
                        tv.setText(read);
                        resetFire();

                    }
                    else if(m.equals("find")){
                        FirebaseDatabase.getInstance().getReference().child("log2") //originally log
                                .addListenerForSingleValueEvent(new ValueEventListener() {
                                    @Override
                                    public void onDataChange(DataSnapshot dataSnapshot) {
                                        //finderobject is stuff from log in firebase
                                        finderobject = new ArrayList<String>();
                                        findertime = new ArrayList<String>();
                                        finderarray = new ArrayList<String>();


                                        for (DataSnapshot snapshot : dataSnapshot.getChildren()) {
                                            String time = snapshot.child("time").getValue(String.class);
                                            String objects = snapshot.child("object").getValue(String.class);
                                            String array = snapshot.child("array").getValue(String.class);
                                            array = array.replace("[", "").replace("]", "").replace("'", "").replace(" ", "");
                                            finderobject.add(objects);
                                            findertime.add(time);
                                            finderarray.add(array);

                                            ArrayList<String> nums = new ArrayList<String>();
                                            for(int i = 0; i < 10; i++)
                                                nums.add(i + "");

                                            String[] ar = array.split(",");
                                            for(String s:ar)
                                            {
                                                if(!allclasses.contains(s) && !nums.contains(s))
                                                {
                                                    allclasses.add(s);
                                                }
                                            }

                                        }
                                        objectSearch = getWord(store.getString(), allclasses);
                                        Log.e("object", objectSearch);
                                        String[] locations = {"Home", "School", "Park", "Library"};
                                        //check each log for word
                                        for (int i = finderobject.size() - 1; i >= 0; i--) {
                                            if (finderobject.get(i).contains(objectSearch)) {
                                                String message = finderarray.get(i);
                                                message = processlog(message); //turns it into the first part of a sentence using log
                                                String t = findertime.get(i);
                                                ///converting the time into x hours and y minutes PM/AM
                                                t = t.replace("AD " , "").replace("EST", "");
                                                t = t.substring(0, t.lastIndexOf(":"));
                                                String[] clocks = t.split(" ");
                                                String clock = clocks[clocks.length-1];
                                                String[] hm = clock.split(":");
                                                int hour = Integer.parseInt(hm[0]);
                                                int min = Integer.parseInt(hm[1]);
                                                String ap = "AM";
                                                if(hour > 12)
                                                    ap = "PM";
                                                hour = hour%12;

                                                String fullclock  = "" + hour + ":" + min + " " +  ap;
                                                String[] btime = t.split(" ");
                                                String finaltime = "";
                                                for(int k  = 0; k < btime.length-1; k++)
                                                    finaltime = finaltime + btime[k] + " ";
                                                finaltime = finaltime + fullclock;

                                                message = message + "on " + finaltime;
                                                if(useLocations == true)
                                                {
                                                   int choose = (int)(Math.random()*locations.length);
                                                    message = message + " at " + locations[choose];
                                                }
                                                tv.setText(message);
                                                speak(message);
                                                found = true;
                                                break;
                                            }
                                        }
                                        if(found == false)
                                        {
                                            speak("Sorry, I did not find that");
                                        }
                                    }

                                    @Override
                                    public void onCancelled(DatabaseError databaseError) {
                                    }

                                });
                        resetFire();

                    }
                    else if(m.equals("scan") || m.equals("skin")){ /////////////done
                        String s = "";
                        if(scan.equals(""))
                            speak("Did not detect");
                        else if(obarray.size() > 1)
                            s = ("there are " + scan);
                        else
                            s = ("there is " + scan);
                        speak(s);
                        resetFire();
                        tv.setText(s);

                    }
                    else if(m.equals("help")){
                        speak("say scan to scan your surroundings, search to search for something near you, find to see when an object was last seen, text to read out text, or ask some other question. Say the word nothing to exit. Say repeat then the mode if you want to hear the same output again");
                        startmode.setValue(0); //so you can redo the prompt
                        tv.setText("help");

                    }
                    else if(m.equals("nothing") || m.equals("nevermind")){
                        speak("Ok");
                        tv.setText("");
                        resetFire();

                    }
                    /*
                    else if(ogtext.contains("how") || ogtext.contains("why") || ogtext.contains("what") || ogtext.contains("where") || ogtext.contains("when"))
                    {g
                        DatabaseReference q = database.getReference("question");
                        q.setValue(ogtext);
                        //mode.setValue(5);
                    }

                    else if(ogtext.contains("repeat") && ogtext.contains("scan"))
                    {
                        speak("There is" + scan);
                        startmode.setValue(0); //so you can redo the prompt

                    }
                    else if(ogtext.contains("repeat") && ogtext.contains("text"))
                    {
                        speak(read);
                        startmode.setValue(0); //so you can redo the prompt

                    }

                    else if(ogtext.contains("repeat") && ogtext.contains("search"))
                    {
                        speak("repeating search");
                        mode.setValue(0);
                        mode.setValue(1);
                    }

                    else if(ogtext.contains("repeat") && ogtext.contains("find"))
                    {
                        speak(read);
                        mode.setValue(0);
                        mode.setValue(3);
                    }
                     */
                    else{
                        speak("Sorry, that's not a valid option");
                        //speak("Sorry, that's not a mode");
                        confirm.setValue(0); //so you can redo the prompt
                        confirm.setValue(1);
                    }

                }

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
class StoreString
{
    private String st = "";

    public void setString(String s)
    {
        st = s;
    }
    public String getString()
    {
        return st;
    }

}