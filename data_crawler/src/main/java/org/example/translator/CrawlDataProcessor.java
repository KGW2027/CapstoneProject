package org.example.translator;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import org.json.simple.JSONArray;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.*;
import java.util.HashSet;

public abstract class CrawlDataProcessor {

    protected TranslatorMachine translator;
    public CrawlDataProcessor(TranslatorMachine translator) {
        this.translator = translator;
    }

    public abstract void process(HashSet<String> texts) throws IOException, ParseException;
    public abstract String getDirectoryName();
    public abstract String getSrcPath();

    protected JSONArray readSource() throws IOException, ParseException {
        String target = getSrcPath();
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(target)));

        StringBuilder read = new StringBuilder();
        String line;
        while( (line = br.readLine()) != null) read.append(line);
        br.close();
        return (JSONArray) new JSONParser().parse(read.toString());
    }

    protected void save(JSONArray result) throws IOException {
        String target = getSrcPath().replace(".json", "-translated.json");
        File file = new File(target);
        if(!file.getParentFile().exists()) file.getParentFile().mkdirs();
        if(!file.exists()) file.createNewFile();

        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        JsonElement ge = JsonParser.parseString(result.toJSONString());
        writer.write(gson.toJson(ge));
        writer.flush();
        writer.close();
    }
}
