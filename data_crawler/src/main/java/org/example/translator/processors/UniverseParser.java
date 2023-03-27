package org.example.translator.processors;

import org.example.translator.CrawlDataProcessor;
import org.example.translator.TranslatorMachine;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.util.HashSet;

public class UniverseParser extends CrawlDataProcessor {
    public UniverseParser(TranslatorMachine translator) {
        super(translator);
    }

    @Override
    public void process(HashSet<String> texts) throws IOException, ParseException {
        JSONArray array = readSource();

        long charCount = 0;

        for(Object o : array) {
            JSONArray ja = (JSONArray) ((JSONObject) ((JSONObject) o).get("data")).get("Header");

            for(Object s : ja) {
                String context = (String) s;

                if(context.length() < 15 || context.split(" ").length < 3) continue;
                charCount += context.length();
                texts.add(context);
            }
        }

        System.out.printf("Sentences : %d [ %,3d chars ]\n", texts.size(), charCount);

    }

    @Override
    public String getDirectoryName() {
        return "UniverseEnTranslated";
    }

    @Override
    public String getSrcPath() {
        return "./data/univ_en/Univ-En.json";
    }
}
