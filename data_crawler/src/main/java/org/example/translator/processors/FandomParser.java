package org.example.translator.processors;

import org.example.DataTree;
import org.example.translator.CrawlDataProcessor;
import org.example.translator.TranslatorMachine;
import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;

public class FandomParser extends CrawlDataProcessor {
    public FandomParser(TranslatorMachine translator) {
        super(translator);
    }

    @Override
    public void process(HashSet<String> texts) throws IOException, ParseException {
        DataTree data = new DataTree(readSource());
        Iterator<String> keys = data.getKeys();
        int idx = 0, max = data.getSize();
        while(keys.hasNext()) {
            System.out.printf("[%04d / %,3d]\n", ++idx, max);

            String key = keys.next();
            List<String> value = data.getValue(key);
            List<String> result = new ArrayList<>();

            for(String v : value) {
//                if(v.length() < 10 || v.split(" ").length < 3) continue;
                List<String> list = translator.appendText(v);
                if(list != null) result.addAll(list);
            }

            List<String> flush = translator.flush();
            if(flush != null) result.addAll(flush);

            if(result.size() > 0)
                data.update(key, result);
//            else
//                data.remove(key);
        }

        save(data.apply());
    }

    @Override
    public String getDirectoryName() {
        return "FandomTranslated";
    }

    @Override
    public String getSrcPath() {
        return "./data/processing/fandom-en-base.json";
    }
}
