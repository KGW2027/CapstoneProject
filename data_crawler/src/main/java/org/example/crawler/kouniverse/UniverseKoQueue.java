package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;

public class UniverseKoQueue extends CrawlingQueue {

    public UniverseKoQueue(String name) {
        super(name);
    }

    private final boolean isKorean = true;

    @Override
    protected String preprocess(String prefix, String url) {
        String url_prefix = isKorean ? "/ko_kr" : "/en_us";
        url = url.startsWith(url_prefix) ? url.replace(url_prefix, "") : url;
        String result = prefix + url;

        if(!result.endsWith("/")) result += '/';
        if(result.endsWith("//")) result = result.substring(0, result.length()-1);

        return result;
    }

    @Override
    public boolean isPreSearch(String url) {
        String replaced = isKorean
                ? url.replace("https://universe.leagueoflegends.com/ko_kr", "")
                : url.replace("https://universe.leagueoflegends.com/en_us", "");
        return replaced.split("/").length < 3;
    }
}
