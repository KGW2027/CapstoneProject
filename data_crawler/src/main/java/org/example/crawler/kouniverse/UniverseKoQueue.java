package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;

public class UniverseKoQueue extends CrawlingQueue {

    public UniverseKoQueue() {
        super();
    }

    private final boolean isKorean = true;

    @Override
    protected String preprocess(String url) {
        String result = "";
        if(isKorean) {
            url = url.startsWith("/ko_kr") ? url.replace("/ko_kr", "") : url;
            result = "https://universe.leagueoflegends.com/ko_kr" + url;
        } else {
            url = url.startsWith("/en_us") ? url.replace("/en_us", "") : url;
            result = "https://universe.leagueoflegends.com/en_us" + url;
        }

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
