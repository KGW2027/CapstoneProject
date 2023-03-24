package org.example.crawler;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;

public class CrawlingDatas extends HashMap<String, Object> {

    private String title, fileName;
    private final String FILE_PARENT = "./data/{title}/{text}.json";

    public CrawlingDatas(String title) {
        this.title = title;
        this.fileName = "";
    }

    private String makeJson() {
        JSONArray array = new JSONArray();
        for(String key : keySet()) {
            Object value = get(key);
            JSONObject jo = new JSONObject();
            jo.put("title", key);

            if(value instanceof CrawlingData)
                jo.put("data", new JSONObject(((CrawlingData) value).getContexts()));
            else if(value instanceof JSONObject)
                jo.put("data", value);

            array.add(jo);
        }
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(array.toJSONString());
        return gson.toJson(ge);
    }

    public void save() throws IOException {
        if(fileName.equals("")) fileName = "save_ckpt";
        String dir = FILE_PARENT.replace("{title}", title).replace("{text}", fileName);
        File file = new File(dir);
        if(!file.getParentFile().exists()) file.getParentFile().mkdirs();
        if(!file.exists()) file.createNewFile();

        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
        writer.write(makeJson());
        writer.flush();
        writer.close();
    }

    private void append(String text) {
        if(fileName.equals("")) fileName = text;
        else fileName = fileName + "-" + text;
    }

    public void clearName() {
        fileName = "";
    }

    public void appendDate() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy_MM_dd_HH_mm_ss");
        append(sdf.format(new Date()));
    }

    public void appendNum(int num) {
        append(String.format("%04d", num));
    }



}
