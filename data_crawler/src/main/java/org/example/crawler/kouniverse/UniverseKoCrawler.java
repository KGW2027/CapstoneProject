package org.example.crawler.kouniverse;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class UniverseKoCrawler {
    public static void main(String[] args) {
        String prefix = "https://universe.leagueoflegends.com/ko_KR";
        CrawlingQueue queue = new UniverseKoQueue();
        new CrawlerBody("univ_ko", prefix, queue, new UniverseKoSearcher())
                .setWaitCss("div.pageLoaded.hidden")
                .start();
    }
}
