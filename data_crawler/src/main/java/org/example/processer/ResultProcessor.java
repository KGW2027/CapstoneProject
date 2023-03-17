package org.example.processer;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.*;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ResultProcessor {

    public static void main(String[] args) throws IOException, ParseException {
        new ResultProcessor("./data/FandomEnTranslated/Fandom-EnKo.json")
                .process();
    }


    private JSONArray array;
    private File output;
    private JSONObject properMap;

    private ResultProcessor(String path) throws IOException, ParseException {

        File properFile = new File("./data/propermap.json");
        BufferedReader propReader = new BufferedReader(new InputStreamReader(new FileInputStream(properFile)));
        String line;
        StringBuilder builder = new StringBuilder();
        while( (line = propReader.readLine()) != null) builder.append(line);
        properMap = (JSONObject) new JSONParser().parse(builder.toString());

        File file = new File(path);
        BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(file)));
        builder.setLength(0);

        while( (line = reader.readLine()) != null) builder.append(line);
        array = (JSONArray) new JSONParser().parse(builder.toString());

        output = new File(path.replace(".json", "process.json"));
        if(!output.exists()) output.createNewFile();
    }

    private void process() {

        HashMap<String, Integer> map = new HashMap<>();
        Pattern ptn = Pattern.compile("[a-zA-Z]+");

        for(Object o : array) {
            String sentence = (String) o;

            for(Object k : properMap.keySet()) {
                String key = (String) k;
                String val = (String) properMap.get(k);
                sentence = sentence.toLowerCase().replace(key.toLowerCase(), val.toLowerCase());
            }

            Matcher matcher = ptn.matcher(sentence);
            while(matcher.find()) {
                String find = matcher.group();
                map.put(find, map.getOrDefault(find, 0)+1);
            }
        }

        for(String k : map.keySet())
            System.out.printf("%s : %d\n", k, map.get(k));

        System.out.printf("\nFOUND NON-FILTERED DATA : %d\n", map.size());
    }
}
