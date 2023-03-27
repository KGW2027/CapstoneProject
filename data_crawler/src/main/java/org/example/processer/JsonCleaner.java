package org.example.processer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.example.DataTree;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

public class JsonCleaner {

    public static void main(String[] args) throws Exception {
        File file = new File("./data/processing/fandom-en-base-translated.json");
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file)));
        StringBuilder sb = new StringBuilder();
        String line;
        while((line = reader.readLine()) != null) sb.append(line);

        JSONArray array = (JSONArray) new JSONParser().parse(sb.toString());

        cleanFandom(array);
    }

    private static void cleanFandom(JSONArray array) throws IOException {
        DataTree tree = new DataTree(array);
        array = tree.apply();

        List<Integer> removedPages = new ArrayList<>();
        for(int idx = 0 ; idx < array.size() ; idx++) {
            JSONObject page = (JSONObject) array.get(idx);

            // Data 유효
            JSONObject data = (JSONObject) page.get("data");
            if(data.size() == 0)
                removedPages.add(idx);

        }

        for(int tgtPage : removedPages) array.remove(tgtPage);

        File save = new File("./data/processing/fandom-en-base-translated-2.json");
        if(!save.exists()) save.createNewFile();

        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(save)));
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(array.toJSONString());
        writer.write(gson.toJson(ge));
        writer.flush();
        writer.close();
    }


}
