package org.example.crawler.fandomen;

import java.io.*;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public class FandomEnCrawlingQueue implements Serializable {

    Queue<String> categories, documents;
    HashSet<String> v_cat, v_docs;

    private boolean categorySaved;
    private final String categoryCache = "./data/FandomEn/category_cache.cache";

    public FandomEnCrawlingQueue() {
        categories = new LinkedList<>();
        documents = new LinkedList<>();
        v_cat = new HashSet<>();
        v_docs = new HashSet<>();

        categorySaved = (new File(categoryCache)).exists();
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
        if(!categorySaved) {
            try {
                saveCache();
            } catch (IOException e) {
                System.out.println("Fandom Cache를 저장하는 중 오류가 발생했습니다.");
                categorySaved = true;
            }
        }
        return documents.poll();
    }

    private void saveCache() throws IOException {
        categorySaved = true;
        File cache = new File(categoryCache);
        if(!cache.exists()) cache.createNewFile();
        ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(cache));
        oos.writeObject(this);
        oos.flush();
        oos.close();
    }

    public FandomEnCrawlingQueue loadCategoryCache() throws IOException, ClassNotFoundException {
        if(!categorySaved) return null;
        File cache = new File(categoryCache);
        ObjectInputStream ois = new ObjectInputStream(new FileInputStream(cache));
        FandomEnCrawlingQueue instance = (FandomEnCrawlingQueue) ois.readObject();
        ois.close();
        return instance;
    }

    public boolean isEmpty() {
        return categories.isEmpty() && documents.isEmpty();
    }

    public int[] size() {
        return new int[]{categories.size(), documents.size()};
    }
}
