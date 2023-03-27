package org.example.processer;

import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.*;

public class UniqueDict {

    private static UniqueDict Instance;

    public static UniqueDict getInstance() {
        return Instance == null ? Instance = new UniqueDict() : Instance;
    }

    JSONObject dict;

    private UniqueDict() {
        File dictFile = new File("./data/propermap.json");
        try {
            BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(dictFile)));
            String line;
            StringBuilder builder = new StringBuilder();
            while((line = reader.readLine()) != null) {
                builder.append(line);
            }
            dict = (JSONObject) new JSONParser().parse(builder.toString());
        } catch (IOException | ParseException e) {
            throw new RuntimeException(e);
        }
    }

    public String replace(String text) {
        text = text.toLowerCase();
        for(Object k : dict.keySet()) {
            String key = (String) k;
            String val = (String) dict.get(k);
            text = text.replace(key.toLowerCase(), val.toLowerCase());
        }
        return text;
    }
}
