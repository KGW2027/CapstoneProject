package org.example.crawler.fandom;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;

public class FandomCrawler {

    public static void main(String[] args) {
        String prefix = "https://leagueoflegends.fandom.com/wiki/";

        CrawlingQueue queue = new FandomQueue();
        new CrawlerBody("univ_en", prefix, queue, new FandomSearcher())
                .setWaitCss("div.pageLoaded.hidden")
                .addQueueManually("/Category:Lore")
                .addBlacklist("comic")
                .start();
    }
}
