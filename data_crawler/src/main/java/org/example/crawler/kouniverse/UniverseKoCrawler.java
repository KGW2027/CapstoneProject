package org.example.crawler.kouniverse;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class UniverseKoCrawler {
    public static void main(String[] args) {

//        String prefix = "https://universe.leagueoflegends.com/ko_KR";
        String prefix = "https://universe.leagueoflegends.com/en_US";

        CrawlingQueue queue = new UniverseKoQueue();
        new CrawlerBody("univ_en", prefix, queue, new UniverseKoSearcher())
                .setWaitCss("div.pageLoaded.hidden")
                .addQueueManually("/champions/")
                .addQueueManually("/regions/")
                .addQueueManually("/odyssey/")
                .addQueueManually("/star-guardian/")
                .addBlacklist("comic")
                .start();
    }
}
