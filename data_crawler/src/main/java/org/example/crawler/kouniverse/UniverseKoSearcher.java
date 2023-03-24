package org.example.crawler.kouniverse;

import org.example.crawler.CrawlerBody;
import org.example.crawler.CrawlingQueue;
import org.example.crawler.CrawlingSearcher;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

public class UniverseKoSearcher extends CrawlingSearcher {

    @Override
    public void search(String docName, CrawlingQueue queue, WebElement element) {

        WebElement appDiv = element.findElement(By.id("App"));
        WebElement contentDiv = appDiv.findElement(By.xpath(".//div[@id='Content']"));
        String inner = contentDiv.getAttribute("innerHTML");

        Document doc = Jsoup.parse(inner);

        // 버튼들을 모두 탐색한 후 Queue에 추가한다.
        Elements linkers = doc.select("a");
        for(Element linker : linkers) {
            String href = linker.attr("href").toLowerCase();
            if(isExternalUrl(href)) continue;
            queue.addQueue(body.URL_PREFIX, href);
        }

        // 문서 정보 획득
//        String[] descs = inner.split("(?=<h[1-2]>)");
        body.addCrawlingData(docName, parseTexts(new String[]{inner}));
    }
}
