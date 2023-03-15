package org.example.crawler;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public class CrawlingQueue {

    private Queue<String> preSearchQueue, postSearchQueue;
    private HashSet<String> searchedSrc;

    protected CrawlingQueue() {
        preSearchQueue = new LinkedList<>();
        postSearchQueue = new LinkedList<>();
        searchedSrc = new HashSet<>();
    }

    private boolean isSearched(String url) {
        boolean searched = searchedSrc.contains(url);
        if(!searched) searchedSrc.add(url);
        return searched;
    }

    protected String preprocess(String url) {
        return url;
    }

    public boolean isPreSearch(String url) {
        return false;
    }

    public void addQueue(String url) {
        url = preprocess(url.toLowerCase());
        if(isSearched(url)) return;

        if(isPreSearch(url)) preSearchQueue.add(url);
        else postSearchQueue.add(url);
    }

    public int[] size() {
        return new int[]{preSearchQueue.size(), postSearchQueue.size()};
    }

    public String poll() {
        return preSearchQueue.size() == 0 ? postSearchQueue.poll() : preSearchQueue.poll();
    }

    public boolean isEmpty() {
        return preSearchQueue.isEmpty() && postSearchQueue.isEmpty();
    }
}
