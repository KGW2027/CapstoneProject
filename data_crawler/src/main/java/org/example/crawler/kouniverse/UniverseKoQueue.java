package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;

public class UniverseKoQueue extends CrawlingQueue {

    public UniverseKoQueue(boolean isKorean) {
        super(String.format("Universe-%s", isKorean?"Ko":"En"));
        this.isKorean = isKorean;
    }

    private final boolean isKorean;

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
        String replaced = url.replace(getPrefix(), "");
        return replaced.split("/").length < 3;
    }

    @Override
    public String getName() {
        return String.format("univ_%s", isKorean?"ko":"en");
    }

    @Override
    public String getPrefix() {
        return isKorean
                ? "https://universe.leagueoflegends.com/ko_kr"
                : "https://universe.leagueoflegends.com/en_us";
    }
}
