package org.example.crawler;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;

public class CrawlingData {

    private String docName;
    private HashMap<String, List<String>> contexts;

    public CrawlingData(String docName) {
        this.docName = docName;
        contexts = new HashMap<>();
    }

    public void add(String key, String... value) {
        List<String> list = new ArrayList<>();
        Collections.addAll(list, value);
        add(key, list);
    }

    public void add(String key, List<String> value) {
        contexts.put(key, value);
    }

    public HashMap<String, List<String>> getContexts() {
        return contexts;
    }
}
