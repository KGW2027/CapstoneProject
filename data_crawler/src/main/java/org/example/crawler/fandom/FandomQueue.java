package org.example.crawler.fandom;

import org.example.crawler.CrawlingQueue;

public class FandomQueue extends CrawlingQueue {
    @Override
    protected String preprocess(String url) {
        return null;
    }

    @Override
    public boolean isPreSearch(String url) {
        return false;
    }
}
