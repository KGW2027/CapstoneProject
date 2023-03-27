package org.example.crawler;

import java.util.LinkedList;
import java.util.Queue;

public class CrawlingQueue {

    Queue<String> categories, documents;

    public CrawlingQueue() {
        categories = new LinkedList<>();
        documents = new LinkedList<>();
    }

    public void add(String url) {
        DocumentType docType = DocumentType.getType(url);
        switch(docType) {
            case Category -> categories.add(url);
            case Document -> documents.add(url);
            default -> System.out.printf("URL [%s]는 분류되지 않은 카테고리입니다.\n", url);
        }
    }

    public String poll() {
        if(categories.size() > 0) return categories.poll();
        return documents.poll();
    }

    public boolean isEmpty() {
        return categories.isEmpty() && documents.isEmpty();
    }

    public int size() {
        return categories.size() + documents.size();
    }
}
