package org.example.crawler.kouniverse;

import org.example.crawler.CrawlingQueue;
import org.example.crawler.CrawlingSearcher;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.openqa.selenium.WebElement;

public class UniverseKoSearcher extends CrawlingSearcher {

    @Override
    public void search(CrawlingQueue queue, WebElement element) {
        super.search(queue, element);

        Document doc = Jsoup.parse(element.getAttribute("innerHTML"));

        Elements linkers = doc.select("a");
        for(Element linker : linkers) {
            String href = linker.attr("href").toLowerCase();
            if(isExternalUrl(href)) continue;
            queue.addQueue(href);
        }
    }
}
