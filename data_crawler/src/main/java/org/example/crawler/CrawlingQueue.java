package org.example.crawler;

import java.io.*;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public abstract class CrawlingQueue {

    private static final String cache_dir = "./data/queue_cache/%s.cache";

    private Queue<String> preSearchQueue, postSearchQueue;
    private HashSet<String> searchedSrc;
    private boolean cached;
    private String name;


    public CrawlingQueue loadCache() {
        File cache = new File(String.format(cache_dir, name));
        if(!cache.exists()) return null;
        try {
            ObjectInputStream ois = new ObjectInputStream(new FileInputStream(cache));
            postSearchQueue = (Queue<String>) ois.readObject();
            searchedSrc = (HashSet<String>) ois.readObject();
            ois.close();
            cached = true;
        } catch (IOException | ClassNotFoundException e) {
            e.printStackTrace();
            throw new RuntimeException(e);
        }
        return this;
    }

    protected CrawlingQueue(String name) {
        preSearchQueue = new LinkedList<>();
        postSearchQueue = new LinkedList<>();
        searchedSrc = new HashSet<>();
        cached = false;
        this.name = name;
    }

    private boolean isSearched(String url) {
        boolean searched = searchedSrc.contains(url);
        if(!searched) searchedSrc.add(url);
        return searched;
    }

    /**
     * 사이트 URL을 통해 주소를 접속가능한 형태로 정제함.
     * @param prefix 주소 접두사
     * @param url 문서 경로
     * @return 정제된 URL
     */
    protected abstract String preprocess(String prefix, String url);

    /**
     * 사이트 URL이 preQueue에 들어갈지 postQueue에 들어갈지 결정함
     * @param url 정제된 주소
     * @return preSearch대상이면 true, 그 외 false
     */
    public abstract boolean isPreSearch(String url);

    public synchronized void addQueue(String prefix, String url) {
        url = preprocess(prefix, url);
        if(isSearched(url)) return;

        String path = url.replace(prefix, "");
        if(path.indexOf('/') == 0) path = path.substring(1);
        if(isPreSearch(path)) preSearchQueue.add(url);
        else postSearchQueue.add(url);
    }

    public synchronized int[] size() {
        return new int[]{preSearchQueue.size(), postSearchQueue.size()};
    }

    public synchronized String poll() {
        if(preSearchQueue.isEmpty() && !postSearchQueue.isEmpty() && !cached) {
            try {
                File cacheFile = new File(String.format(cache_dir, name));
                if(!cacheFile.getParentFile().exists()) cacheFile.getParentFile().mkdirs();
                if(!cacheFile.exists()) cacheFile.createNewFile();

                ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(String.format(cache_dir, name)));
                oos.writeObject(postSearchQueue);
                oos.writeObject(searchedSrc);
                oos.flush();
                oos.close();
                cached = true;
                System.out.println("POST 캐시 저장에 완료하였습니다.");
            } catch (IOException e) {
                System.out.println("Cache 저장에 실패하였습니다.");
                e.printStackTrace();
            }
        }

        return preSearchQueue.size() == 0 ? postSearchQueue.poll() : preSearchQueue.poll();
    }

    public synchronized boolean isEmpty() {
        return preSearchQueue.isEmpty() && postSearchQueue.isEmpty();
    }
}
