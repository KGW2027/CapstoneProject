package org.example.translator.processors;

import org.example.translator.CrawlDataProcessor;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.util.*;

public class FandomJSONParser extends CrawlDataProcessor {

    private final String[] except_categories = {
        "turrets", "summoner", "event", "daily", "teamfight tactics", "co-op vs", "login", "shop", "milestones", "runes", "when ten", "announcements", "upgrade"
    };

    private final String[] except_contains = {
            "https", "category:", "page:", "file:", "image:", "audio:", "video:", "(TBA)", ".ogg", ".mp4", "points:", "(based on", "objective:", "#"
    };

    class SetData implements Comparable<SetData> {
        String key;
        int values;
        List<JSONArray> sentences;

        public SetData(String key) {
            this.key = key;
            values = 0;
            sentences = new ArrayList<>();
        }

        @Override
        public int compareTo(SetData o) {
            return Integer.compare(values, o.values);
        }
    }

    @Override
    public void process(HashSet<String> texts) throws ParseException, IOException {
        JSONArray json = readSource();

        HashSet<String> categories = new HashSet<>();
        HashMap<String, SetData> map = new HashMap<>();

        for(Object o : json) {
            JSONObject jo = (JSONObject) ((JSONObject) o).get("data");
            keyloop:for (Object k : jo.keySet()) {

                String key = k.toString().toLowerCase();

                for (String except : except_categories) {
                    if (key.contains(except)) continue keyloop;
                }

                JSONArray v = (JSONArray) jo.get(k);
                if(v.size() == 0) continue;
                if(key.split(" ").length > 3) continue;

                SetData sd = map.getOrDefault(key, new SetData(key));
                sd.values += v.size();
                sd.sentences.add(v);
                map.put(key, sd);

                categories.add(key);

            }
        }

        long charCount = 0L;

        for(SetData sd : map.values()) {
            if(sd.values < 10) continue;
            if(sd.sentences.size() <= 1) continue;

            for(JSONArray array : sd.sentences) {
                lineloop:for(Object o : array) {
                    String line = ((String) o).toLowerCase();
                    
                    // 무의미한 텍스트 개수 줄이기
                    if(line.split(" ").length <= 3) continue;
//                    if(line.length() < 20) continue;

                    for(String except : except_contains)
                        if(line.contains(except.toLowerCase())) continue lineloop;

                    // 각주(Footnote) 제거
                    line = line.replaceAll("[d+]", "");
                    texts.add(line);
                    charCount += line.length();
                }
            }
        }

        System.out.printf("Sentences : %d [ %,3d chars ]\n", texts.size(), charCount);

    }

    @Override
    public String getDirectoryName() {
        return "FandomEnTranslated";
    }

    @Override
    public String getSrcPath() {
        return "./data/FandomEn/lolwiki_2574.json";
    }
}
