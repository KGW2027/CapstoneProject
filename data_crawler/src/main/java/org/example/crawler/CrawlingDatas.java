package org.example.crawler;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.io.*;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;

public class CrawlingDatas extends HashMap<String, CrawlingData> {

    private String title;
    private final String FILE_PARENT = "./data/{title}/{text}.json";

    public CrawlingDatas(String title) {
        this.title = title;
    }

    private String makeJson() {
        JSONArray array = new JSONArray();
        for(String key : keySet()) {
            JSONObject jo = new JSONObject();
            jo.put("title", key);
            jo.put("data", new JSONObject(get(key).getContexts()));
            array.add(jo);
        }
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(array.toJSONString());
        return gson.toJson(ge);
    }

    public void save(String name) throws IOException {
        String dir = FILE_PARENT.replace("{title}", title).replace("{text}", name);
        File file = new File(dir);
        file.mkdir();
        if(!file.exists()) file.createNewFile();

        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
        writer.write(makeJson());
        writer.flush();
        writer.close();
    }

    public void saveWithDate() throws IOException {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd-saves");
        save(sdf.format(new Date()));
    }



}
