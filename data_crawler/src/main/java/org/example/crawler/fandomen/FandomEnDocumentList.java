package org.example.crawler.fandomen;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.io.*;
import java.util.HashMap;
import java.util.List;

public class FandomEnDocumentList {

    private static FandomEnDocumentList instance;

    public static FandomEnDocumentList getInstance() {
        return instance == null ? instance = new FandomEnDocumentList() : instance;
    }

    private HashMap<String, HashMap<String, List<String>>> results;
    private final String FILE_PATH = "data/FandomEn/lolwiki_{size}.json";

    private FandomEnDocumentList() {
        results = new HashMap<>();
    }

    public void addDocument(String docName, HashMap<String, List<String>> contexts) {
        results.put(docName, contexts);
        if(results.size() % 100 == 0) {
            try {
                save();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }

    public void save() throws IOException {
        File file = new File(FILE_PATH.replace("{size}", String.valueOf(results.size())));
        if(!file.exists()) {
            file.createNewFile();
        }

        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
        JSONArray json = new JSONArray();
        for(String key : results.keySet()) {
            JSONObject jo = new JSONObject();
            jo.put("doc_name", key);
            jo.put("data", new JSONObject(results.get(key)));
            json.add(jo);
        }

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(json.toJSONString());
        writer.write(gson.toJson(ge));
        writer.flush();
        writer.close();
        System.out.printf("Saved on %s\n", file.getCanonicalPath());
    }
}
