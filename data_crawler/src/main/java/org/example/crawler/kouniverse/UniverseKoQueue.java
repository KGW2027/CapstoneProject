package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;

public class UniverseKoQueue extends CrawlingQueue {

    public UniverseKoQueue() {
        super();
    }

    @Override
    protected String preprocess(String url) {

        url = url.startsWith("/ko_kr") ? url.replace("/ko_kr", "") : url;
        String result = "https://universe.leagueoflegends.com/ko_kr" + url;

        if(!result.endsWith("/")) result += '/';
        if(result.endsWith("//")) result = result.substring(0, result.length()-1);

        return result;
    }

    @Override
    public boolean isPreSearch(String url) {
        String replaced = url.replace("https://universe.leagueoflegends.com/ko_kr", "");
        return replaced.split("/").length < 3;
    }
}
