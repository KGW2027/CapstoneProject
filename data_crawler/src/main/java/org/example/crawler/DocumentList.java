package org.example.crawler;

import java.util.HashMap;
import java.util.List;

public class DocumentList {

    private static DocumentList instance;

    public static DocumentList getInstance() {
        return instance == null ? instance = new DocumentList() : instance;
    }

    private HashMap<String, HashMap<String, List<String>>> results;

    private DocumentList() {
        results = new HashMap<>();
    }

    public void addDocument(String docName, HashMap<String, List<String>> contexts) {
        results.put(docName, contexts);
    }

    public void save() {
        System.out.println(results.size());
    }
}
