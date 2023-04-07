package org.example.crawler.fandom;

import org.example.crawler.CrawlingQueue;

public class FandomQueue extends CrawlingQueue {
    protected FandomQueue(String name) {
        super(name);
        this.name = name.toLowerCase();
    }

    private final String name;

    @Override
    protected String preprocess(String prefix, String url) {
        return url.startsWith(prefix) ? url : prefix + url;
    }

    @Override
    public boolean isPreSearch(String url) {
        return url.toLowerCase().startsWith("category:");
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public String getPrefix() {
        return "https://leagueoflegends.fandom.com/wiki";
    }
}
