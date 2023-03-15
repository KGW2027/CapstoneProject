package org.example.crawler.fandomen;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public class FandomEnCrawlingQueue {

    Queue<String> categories, documents;
    HashSet<String> v_cat, v_docs;

    public FandomEnCrawlingQueue() {
        categories = new LinkedList<>();
        documents = new LinkedList<>();
        v_cat = new HashSet<>();
        v_docs = new HashSet<>();
    }

    public void add(String url) {
        FandomEnDocumentType docType = FandomEnDocumentType.getType(url);
        if(docType == FandomEnDocumentType.Category) {
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
        // 카테고리 문서는 총 707개, 크롤링 대상 문서는 4140개
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
