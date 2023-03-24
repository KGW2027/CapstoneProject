package org.example.crawler.fandom;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class FandomCrawler {

    public static void main(String[] args) {
        String prefix = "https://leagueoflegends.fandom.com/wiki";
        String key = "Fandom";

        CrawlingQueue queue = new FandomQueue(key)
//                .loadCache()
                ;
        new CrawlerBody("fandom", prefix, queue, new FandomSearcher())
                .addQueueManually("/Category:Lore")
                .setThreadCount(4)
                .setHeadless()
                .start();
    }
}
