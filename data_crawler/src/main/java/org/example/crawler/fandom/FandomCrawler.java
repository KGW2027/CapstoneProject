package org.example.crawler.fandom;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class FandomCrawler {

    public static void main(String[] args) {

        FandomQueue queue = new FandomQueue("Fandom");
        queue.setSavemode(false)
                .loadCache()
                ;
        new CrawlerBody(queue, new FandomSearcher())
//                .addQueueManually("/Category:Lore")
//                .addQueueManually("/Crystal_Scar")
                .setThreadCount(4)
                .setHeadless()
                .start();
    }
}
