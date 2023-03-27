package org.example.crawler.fandom;

import org.example.crawler.CrawlingQueue;

public class FandomQueue extends CrawlingQueue {
    protected FandomQueue(String name) {
        super(name);
    }

    @Override
    protected String preprocess(String prefix, String url) {
        return url.startsWith(prefix) ? url : prefix + url;
    }

    @Override
    public boolean isPreSearch(String url) {
        return url.toLowerCase().startsWith("category:");
    }
}
