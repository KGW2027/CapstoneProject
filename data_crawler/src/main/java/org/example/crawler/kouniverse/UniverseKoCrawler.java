package org.example.crawler.kouniverse;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class UniverseKoCrawler {
    public static void main(String[] args) {

        boolean korean = true;

        UniverseKoQueue queue = new UniverseKoQueue(korean);
        new CrawlerBody(queue, new UniverseKoSearcher())
                .setWaitCss("div.pageLoaded.hidden")
                .addQueueManually("/champions/")
                .addQueueManually("/regions/")
//                .addQueueManually("/odyssey/")
//                .addQueueManually("/star-guardian/")
                .addBlacklist("comic")
                .start();
    }
}
