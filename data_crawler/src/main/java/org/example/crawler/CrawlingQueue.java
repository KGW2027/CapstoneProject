package org.example.crawler;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public class CrawlingQueue {

    Queue<String> categories, documents;
    HashSet<String> v_cat, v_docs;

    public CrawlingQueue() {
        categories = new LinkedList<>();
        documents = new LinkedList<>();
        v_cat = new HashSet<>();
        v_docs = new HashSet<>();
    }

    public void add(String url) {
        DocumentType docType = DocumentType.getType(url);
        if(docType == DocumentType.Category) {
            if(v_cat.contains(url)) return;
            v_cat.add(url);
            categories.add(url);
        }
        else if(docType.isDocument) {
            if (v_docs.contains(url)) return;
            v_docs.add(url);
            documents.add(url);
        }
    }

    public String poll() {
        if(categories.size() > 0) return categories.poll();
        System.out.println(Categories.getInstance().categoryMap.size());
        return documents.poll();
    }

    public boolean isEmpty() {
        return categories.isEmpty() && documents.isEmpty();
    }

    public int size() {
        return categories.size() + documents.size();
    }
}
