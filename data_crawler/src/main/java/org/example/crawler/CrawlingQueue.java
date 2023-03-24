package org.example.crawler;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public abstract class CrawlingQueue {

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

    public void addQueue(String prefix, String url) {
        url = preprocess(prefix, url.toLowerCase());
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
